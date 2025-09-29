package com.oppo.fastapicrudbooster.ui

import com.intellij.openapi.fileChooser.FileChooser
import com.intellij.openapi.fileChooser.FileChooserDescriptor
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.DialogWrapper
import com.intellij.openapi.ui.Messages
import com.intellij.openapi.vfs.VirtualFile
import com.intellij.ui.ToolbarDecorator
import com.intellij.ui.components.JBTextField
import com.intellij.ui.dsl.builder.AlignX
import com.intellij.ui.dsl.builder.panel
import com.intellij.ui.table.JBTable
import com.oppo.fastapicrudbooster.gen.CrudGenerator
import com.oppo.fastapicrudbooster.state.CrudGenerationState
import com.oppo.fastapicrudbooster.state.CrudYamlParser
import com.oppo.fastapicrudbooster.state.EntityDefinition
import com.oppo.fastapicrudbooster.state.FieldDefinition
import com.oppo.fastapicrudbooster.state.GeneratorSettings
import java.awt.BorderLayout
import java.awt.Dimension
import javax.swing.DefaultCellEditor
import javax.swing.JComboBox
import javax.swing.JComponent
import javax.swing.JPanel
import javax.swing.table.AbstractTableModel
import javax.swing.table.DefaultTableCellRenderer

/**
 * Multi-step wizard dialog collecting entity metadata, YAML import and preview operations.
 */
class CrudWizardDialog(private val project: Project, private val basePath: String) : DialogWrapper(project) {
    private val entityNameField = JBTextField()
    private val tableNameField = JBTextField()
    private val descriptionField = JBTextField()
    private val sqlalchemyCombo = JComboBox(arrayOf("2.0", "1.4"))
    private val pydanticCombo = JComboBox(arrayOf("2", "1"))
    private val paginationCombo = JComboBox(arrayOf("enabled", "disabled"))
    private val filtersCombo = JComboBox(arrayOf("enabled", "disabled"))
    private val featureFlagsCombo = JComboBox(arrayOf("enabled", "disabled"))

    private val fieldTableModel = CrudFieldTableModel()
    private val fieldTable = JBTable(fieldTableModel)

    init {
        title = "FastAPI CRUD Booster"
        init()
        initTable()
        addAction(PreviewDiffAction())
        addAction(ImportYamlAction())
    }

    override fun createCenterPanel(): JComponent {
        val wrapper = JPanel(BorderLayout())
        wrapper.preferredSize = Dimension(860, 600)
        wrapper.add(buildForm(), BorderLayout.NORTH)
        wrapper.add(buildTablePanel(), BorderLayout.CENTER)
        return wrapper
    }

    fun generate(): CrudGenerator.GenerationResult {
        val state = collectState()
        val generator = CrudGenerator(project, basePath)
        return generator.generate(state)
    }

    private fun collectState(): CrudGenerationState {
        val entity = EntityDefinition(
            name = entityNameField.text.trim(),
            tableName = tableNameField.text.trim(),
            description = descriptionField.text.trim(),
            fields = fieldTableModel.items.toList()
        )

        val settings = GeneratorSettings(
            sqlalchemyMajor = sqlalchemyCombo.selectedItem.toString().substringBefore('.').toInt(),
            pydanticMajor = pydanticCombo.selectedItem.toString().toInt(),
            enablePagination = paginationCombo.selectedItem == "enabled",
            enableFilters = filtersCombo.selectedItem == "enabled",
            enableFeatureFlags = featureFlagsCombo.selectedItem == "enabled"
        )

        return CrudGenerationState(entity = entity, settings = settings)
    }

    private fun buildForm(): JComponent = panel {
        row("Entity name") {
            cell(entityNameField).align(AlignX.FILL)
        }
        row("Table name") {
            cell(tableNameField).align(AlignX.FILL)
        }
        row("Description") {
            cell(descriptionField).align(AlignX.FILL)
        }
        row("SQLAlchemy") {
            cell(sqlalchemyCombo)
            comment("Выберите целевую мажорную версию SQLAlchemy")
        }
        row("Pydantic") {
            cell(pydanticCombo)
        }
        row("Pagination") {
            cell(paginationCombo)
        }
        row("Filters") {
            cell(filtersCombo)
        }
        row("Feature flags") {
            cell(featureFlagsCombo)
        }
    }

    private fun buildTablePanel(): JComponent {
        fieldTable.rowHeight = 28
        fieldTable.preferredScrollableViewportSize = Dimension(600, 280)
        val panel = ToolbarDecorator.createDecorator(fieldTable)
            .setAddAction { fieldTableModel.addRow() }
            .setRemoveAction {
                val index = fieldTable.selectedRow
                if (index >= 0) {
                    fieldTableModel.removeRow(index)
                }
            }
            .createPanel()
        (panel.layout as? BorderLayout)?.vgap = 8
        return panel
    }

    private fun initTable() {
        fieldTable.columnModel.getColumn(1).cellEditor = DefaultCellEditor(JComboBox(arrayOf(
            "int", "float", "decimal", "str", "bool", "date", "datetime"
        )))
        val booleanRenderer = DefaultTableCellRenderer().apply { horizontalAlignment = javax.swing.SwingConstants.CENTER }
        val booleanEditor = DefaultCellEditor(JComboBox(arrayOf("false", "true")))
        fieldTable.columnModel.getColumn(2).cellEditor = booleanEditor
        fieldTable.columnModel.getColumn(2).cellRenderer = booleanRenderer
        fieldTable.columnModel.getColumn(3).cellEditor = booleanEditor
        fieldTable.columnModel.getColumn(3).cellRenderer = booleanRenderer
        fieldTable.columnModel.getColumn(5).cellEditor = booleanEditor
        fieldTable.columnModel.getColumn(5).cellRenderer = booleanRenderer
    }

    private inner class PreviewDiffAction : DialogWrapperAction("Preview Diff") {
        override fun doAction(e: java.awt.event.ActionEvent?) {
            val state = collectState()
            val generator = CrudGenerator(project, basePath)
            val preview = generator.preview(state)
            DiffViewerHelper.show(project, preview)
        }
    }

    private inner class ImportYamlAction : DialogWrapperAction("Import crudgen.yaml") {
        override fun doAction(e: java.awt.event.ActionEvent?) {
            val descriptor = FileChooserDescriptor(true, false, false, false, false, false)
                .withFileFilter { it.name == "crudgen.yaml" }
            val file: VirtualFile? = FileChooser.chooseFile(descriptor, project, null)
            if (file != null) {
                try {
                    file.inputStream.use {
                        val state = CrudYamlParser.parse(it)
                        applyState(state)
                    }
                } catch (ex: Exception) {
                    Messages.showErrorDialog(project, "Не удалось импортировать crudgen.yaml: ${ex.message}", "Импорт YAML")
                }
            }
        }
    }

    private fun applyState(state: CrudGenerationState) {
        entityNameField.text = state.entity.name
        tableNameField.text = state.entity.tableName
        descriptionField.text = state.entity.description
        sqlalchemyCombo.selectedItem = "${state.settings.sqlalchemyMajor}.0"
        pydanticCombo.selectedItem = state.settings.pydanticMajor.toString()
        paginationCombo.selectedItem = if (state.settings.enablePagination) "enabled" else "disabled"
        filtersCombo.selectedItem = if (state.settings.enableFilters) "enabled" else "disabled"
        featureFlagsCombo.selectedItem = if (state.settings.enableFeatureFlags) "enabled" else "disabled"

        fieldTableModel.setItems(state.entity.fields)
    }
}

private class CrudFieldTableModel : AbstractTableModel() {
    private val columnNames = arrayOf("Name", "Type", "Nullable", "Unique", "Default", "Indexed", "Description")
    val items: MutableList<FieldDefinition> = mutableListOf()

    fun addRow() {
        items.add(FieldDefinition(name = "field${items.size + 1}", type = "str"))
        fireTableDataChanged()
    }

    fun removeRow(index: Int) {
        if (index in items.indices) {
            items.removeAt(index)
            fireTableDataChanged()
        }
    }

    fun setItems(fields: List<FieldDefinition>) {
        items.clear()
        items.addAll(fields)
        fireTableDataChanged()
    }

    override fun getRowCount(): Int = items.size

    override fun getColumnCount(): Int = columnNames.size

    override fun getColumnName(column: Int): String = columnNames[column]

    override fun getValueAt(rowIndex: Int, columnIndex: Int): Any {
        val item = items[rowIndex]
        return when (columnIndex) {
            0 -> item.name
            1 -> item.type
            2 -> item.nullable
            3 -> item.unique
            4 -> item.defaultValue ?: ""
            5 -> item.indexed
            6 -> item.description ?: ""
            else -> ""
        }
    }

    override fun isCellEditable(rowIndex: Int, columnIndex: Int): Boolean = true

    override fun setValueAt(aValue: Any?, rowIndex: Int, columnIndex: Int) {
        val value = aValue?.toString() ?: ""
        val item = items[rowIndex]
        when (columnIndex) {
            0 -> items[rowIndex] = item.copy(name = value)
            1 -> items[rowIndex] = item.copy(type = value)
            2 -> items[rowIndex] = item.copy(nullable = value.toBoolean())
            3 -> items[rowIndex] = item.copy(unique = value.toBoolean())
            4 -> items[rowIndex] = item.copy(defaultValue = value.ifEmpty { null })
            5 -> items[rowIndex] = item.copy(indexed = value.toBoolean())
            6 -> items[rowIndex] = item.copy(description = value.ifEmpty { null })
        }
        fireTableRowsUpdated(rowIndex, rowIndex)
    }
}

private object DiffViewerHelper {
    fun show(project: Project, result: CrudGenerator.GenerationResult) {
        val diffManager = com.intellij.openapi.diff.DiffManager.getInstance()
        result.files.forEach { file ->
            val existing = file.existingContent ?: ""
            val request = com.intellij.diff.requests.SimpleDiffRequest(
                "Preview ${file.relativePath}",
                com.intellij.diff.contents.DiffContentFactory.getInstance().create(existing),
                com.intellij.diff.contents.DiffContentFactory.getInstance().create(file.content),
                "Существующий", "Новый"
            )
            diffManager.showDiff(project, request)
        }
    }
}
