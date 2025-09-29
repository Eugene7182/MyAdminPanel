plugins {
    id("org.jetbrains.intellij") version "1.16.0"
    kotlin("jvm") version "1.9.22"
}

group = "com.oppo.fastapicrudbooster"
version = "1.0.0"

repositories {
    mavenCentral()
}

dependencies {
    implementation("org.freemarker:freemarker:2.3.32")
    implementation("org.yaml:snakeyaml:2.2")
}

intellij {
    version.set("2023.3")
    type.set("IC")
    plugins.set(listOf("com.intellij.java", "Pythonid"))
}

kotlin {
    jvmToolchain(17)
}

tasks {
    patchPluginXml {
        sinceBuild.set("233")
        untilBuild.set("241.*")
        changeNotes.set("<ul><li>Initial release with FastAPI CRUD wizard.</li></ul>")
    }

    signPlugin {
        certificateChainFile.set(System.getenv("JETBRAINS_CERTIFICATE_CHAIN"))
        privateKeyFile.set(System.getenv("JETBRAINS_PRIVATE_KEY"))
        password.set(System.getenv("JETBRAINS_PRIVATE_KEY_PASSWORD"))
    }

    publishPlugin {
        token.set(System.getenv("JETBRAINS_MARKETPLACE_TOKEN"))
        channels.set(listOf("Stable"))
    }
}
