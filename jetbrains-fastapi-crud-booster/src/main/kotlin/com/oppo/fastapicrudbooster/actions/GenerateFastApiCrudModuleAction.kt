package com.oppo.fastapicrudbooster.actions

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.extensions.PluginId
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.Messages
import com.oppo.fastapicrudbooster.state.MarketplaceLicenseService
import com.oppo.fastapicrudbooster.ui.CrudWizardDialog

/**
 * Entry point for the "Generate FastAPI CRUD Module" action available from the New group.
 */
class GenerateFastApiCrudModuleAction : AnAction() {
    private val logger = Logger.getInstance(GenerateFastApiCrudModuleAction::class.java)
    private val pluginId = PluginId.getId("com.oppo.fastapicrudbooster")

    override fun actionPerformed(event: AnActionEvent) {
        val project = event.project ?: return
        val virtualFile = event.getData(CommonDataKeys.VIRTUAL_FILE) ?: return

        if (!MarketplaceLicenseService.getInstance().ensureActive(pluginId)) {
            Messages.showErrorDialog(project, "Лицензия JetBrains Marketplace для FastAPI CRUD Booster неактивна.", "Лицензия не подтверждена")
            return
        }

        showWizard(project, virtualFile.path)
    }

    override fun update(event: AnActionEvent) {
        event.presentation.isEnabledAndVisible = event.project != null
    }

    private fun showWizard(project: Project, targetPath: String) {
        val dialog = CrudWizardDialog(project, targetPath)
        if (dialog.showAndGet()) {
            val result = dialog.generate()
            if (result.errors.isNotEmpty()) {
                val message = result.errors.joinToString(separator = "\n")
                logger.warn("Generation finished with errors: $message")
                Messages.showErrorDialog(project, message, "FastAPI CRUD Booster")
            } else {
                Messages.showInfoMessage(project, "CRUD модуль успешно создан.", "FastAPI CRUD Booster")
            }
        }
    }
}
