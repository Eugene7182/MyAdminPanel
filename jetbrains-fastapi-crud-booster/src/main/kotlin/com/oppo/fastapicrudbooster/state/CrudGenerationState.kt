package com.oppo.fastapicrudbooster.state

import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.Constructor
import java.io.InputStream

/**
 * DTO describing a CRUD generation request prepared by the wizard.
 */
data class CrudGenerationState(
    val entity: EntityDefinition,
    val settings: GeneratorSettings,
    val sourceYaml: String? = null
)

/**
 * Representation of entity schema defined either in the wizard or via YAML import.
 */
data class EntityDefinition(
    val name: String,
    val tableName: String,
    val description: String,
    val fields: List<FieldDefinition>
)

/**
 * Field metadata used to fill FreeMarker templates.
 */
data class FieldDefinition(
    val name: String,
    val type: String,
    val nullable: Boolean = false,
    val unique: Boolean = false,
    val defaultValue: String? = null,
    val indexed: Boolean = false,
    val description: String? = null
)

/**
 * Advanced generation toggles that align with OPPO KZ platform roadmap.
 */
data class GeneratorSettings(
    val sqlalchemyMajor: Int = 2,
    val pydanticMajor: Int = 2,
    val enablePagination: Boolean = true,
    val enableFilters: Boolean = true,
    val enableFeatureFlags: Boolean = true
)

/**
 * YAML payload root.
 */
data class CrudGenYaml(
    val entity: EntityYaml,
    val settings: YamlSettings? = null
)

data class EntityYaml(
    val name: String,
    val table: String,
    val description: String,
    val fields: List<YamlField>
)

data class YamlField(
    val name: String,
    val type: String,
    val nullable: Boolean = false,
    val unique: Boolean = false,
    val default: String? = null,
    val indexed: Boolean = false,
    val description: String? = null
)

data class YamlSettings(
    val sqlalchemy: Int = 2,
    val pydantic: Int = 2,
    val pagination: Boolean = true,
    val filters: Boolean = true,
    val featureFlags: Boolean = true
)

/**
 * Parses a YAML config stream into internal state.
 */
object CrudYamlParser {
    fun parse(stream: InputStream): CrudGenerationState {
        val yamlText = stream.bufferedReader().use { it.readText() }
        val yaml = Yaml(Constructor(CrudGenYaml::class.java))
        val root = yaml.load<CrudGenYaml>(yamlText)
            ?: throw IllegalArgumentException("crudgen.yaml is empty")

        val entity = EntityDefinition(
            name = root.entity.name,
            tableName = root.entity.table,
            description = root.entity.description,
            fields = root.entity.fields.map {
                FieldDefinition(
                    name = it.name,
                    type = it.type,
                    nullable = it.nullable,
                    unique = it.unique,
                    defaultValue = it.default,
                    indexed = it.indexed,
                    description = it.description
                )
            }
        )

        val settings = GeneratorSettings(
            sqlalchemyMajor = root.settings?.sqlalchemy ?: 2,
            pydanticMajor = root.settings?.pydantic ?: 2,
            enablePagination = root.settings?.pagination ?: true,
            enableFilters = root.settings?.filters ?: true,
            enableFeatureFlags = root.settings?.featureFlags ?: true
        )

        return CrudGenerationState(entity = entity, settings = settings, sourceYaml = yamlText)
    }
}
