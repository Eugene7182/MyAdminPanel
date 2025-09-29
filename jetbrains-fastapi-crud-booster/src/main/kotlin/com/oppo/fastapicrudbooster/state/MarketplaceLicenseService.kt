package com.oppo.fastapicrudbooster.state

import com.intellij.openapi.components.Service
import com.intellij.openapi.components.service
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.extensions.PluginId

/**
 * Thin wrapper around JetBrains Marketplace licensing service.
 * The service is invoked from the action entry point to prevent unauthorised usage.
 */
@Service(Service.Level.APP)
class MarketplaceLicenseService {
    private val logger = Logger.getInstance(MarketplaceLicenseService::class.java)

    fun ensureActive(pluginId: PluginId): Boolean {
        return try {
            val serviceClass = Class.forName("com.jetbrains.commercial.licenseVerification.api.LicenseCheckingService")
            val getInstance = serviceClass.getMethod("getInstance")
            val instance = getInstance.invoke(null)
            val method = serviceClass.getMethod("checkPluginLicense", PluginId::class.java)
            method.invoke(instance, pluginId) as Boolean
        } catch (ex: ClassNotFoundException) {
            logger.warn("Marketplace licensing API not available. Allowing plugin execution for sandbox.", ex)
            true
        } catch (ex: Exception) {
            logger.warn("Marketplace license validation failed", ex)
            false
        }
    }

    companion object {
        fun getInstance(): MarketplaceLicenseService = service()
    }
}
