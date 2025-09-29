package com.oppo.fastapicrudbooster.gen

import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.LocalFileSystem
import com.intellij.openapi.vfs.VfsUtil
import com.oppo.fastapicrudbooster.state.CrudGenerationState
import freemarker.template.Configuration
import freemarker.template.TemplateExceptionHandler
import java.io.StringWriter
import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.nio.file.Path
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/**
 * Generates FastAPI CRUD scaffolding using FreeMarker templates.
 */
class CrudGenerator(private val project: Project, private val basePath: String) {
    private val logger = Logger.getInstance(CrudGenerator::class.java)
    private val config = Configuration(Configuration.VERSION_2_3_32).apply {
        setClassLoaderForTemplateLoading(javaClass.classLoader, "templates")
        defaultEncoding = StandardCharsets.UTF_8.name()
        templateExceptionHandler = TemplateExceptionHandler.RETHROW_HANDLER
        wrapUncheckedExceptions = true
    }

    data class GeneratedFile(
        val relativePath: String,
        val absolutePath: Path,
        val content: String,
        val existingContent: String? = null
    )

    data class GenerationResult(
        val files: List<GeneratedFile>,
        val errors: List<String>
    )

    fun preview(state: CrudGenerationState): GenerationResult {
        val generatedFiles = renderAll(state)
        val errors = mutableListOf<String>()
        return GenerationResult(generatedFiles, errors)
    }

    fun generate(state: CrudGenerationState): GenerationResult {
        val generatedFiles = renderAll(state)
        val errors = mutableListOf<String>()

        generatedFiles.forEach { file ->
            try {
                val merged = mergeWithGuards(file.absolutePath, file.content)
                Files.createDirectories(file.absolutePath.parent)
                Files.writeString(file.absolutePath, merged, StandardCharsets.UTF_8)
                refreshVfs(file.absolutePath)
            } catch (ex: IllegalStateException) {
                logger.warn("Guard merge aborted for ${file.relativePath}", ex)
                errors.add(ex.message ?: "Не удалось обновить ${file.relativePath}")
            } catch (ex: Exception) {
                logger.warn("Failed to write ${file.relativePath}", ex)
                errors.add("Ошибка записи ${file.relativePath}: ${ex.message}")
            }
        }

        return GenerationResult(generatedFiles, errors)
    }

    private fun renderAll(state: CrudGenerationState): List<GeneratedFile> {
        val context = mapOf(
            "entity" to state.entity,
            "settings" to state.settings,
            "timestamp" to LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmm"))
        )

        val entitySnake = state.entity.name.lowercase()
        val files = listOf(
            "models/${entitySnake}.py" to "models.ftl",
            "schemas/${entitySnake}.py" to "schemas.ftl",
            "crud/${entitySnake}.py" to "crud.ftl",
            "routes/${entitySnake}.py" to "routes.ftl",
            "tests/test_${entitySnake}.py" to "tests.ftl",
            "alembic/versions/${context["timestamp"]}_${entitySnake}.py" to "alembic.ftl",
            "README.md" to "readme.ftl"
        )

        return files.map { (relative, templateName) ->
            val template = config.getTemplate(templateName)
            val writer = StringWriter()
            template.process(context, writer)
            val absolute = Path.of(basePath, relative)
            val existing = if (Files.exists(absolute)) Files.readString(absolute) else null
            GeneratedFile(relative, absolute, writer.toString(), existing)
        }
    }

    private fun mergeWithGuards(path: Path, generated: String): String {
        if (!Files.exists(path)) {
            return generated
        }
        val existing = Files.readString(path)
        val guardBegin = "# >>> FASTAPI_CRUD_BOOSTER"
        val guardEnd = "# <<< FASTAPI_CRUD_BOOSTER"

        if (!existing.contains(guardBegin) || !existing.contains(guardEnd)) {
            throw IllegalStateException("Файл ${path.fileName} уже существует и не содержит guard-блоков.")
        }

        val existingPrefix = existing.substringBefore(guardBegin)
        val existingSuffix = existing.substringAfter(guardEnd)

        val generatedSegment = generated.substringAfter(guardBegin, missingDelimiterValue = "")
            .substringBeforeLast(guardEnd, missingDelimiterValue = "")
        if (generatedSegment.isEmpty()) {
            throw IllegalStateException("Сгенерированный файл ${path.fileName} не содержит guard-блоков.")
        }

        return buildString {
            append(existingPrefix)
            append(guardBegin)
            append("\n")
            append(generatedSegment.trim())
            append("\n")
            append(guardEnd)
            append(existingSuffix)
        }
    }

    private fun refreshVfs(path: Path) {
        val local = LocalFileSystem.getInstance().refreshAndFindFileByIoFile(path.toFile())
        local?.let { VfsUtil.markDirtyAndRefresh(true, false, false, it) }
    }
}
