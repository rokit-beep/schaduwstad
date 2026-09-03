package com.nightforge.schaduwstad.data

import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class IsolationParseTest {
    private val json = Json { ignoreUnknownKeys = true }

    @Test
    fun detectiveViewMustNotCarryMafiaChat() {
        val raw = """
            {"lobbyCode":"AB12","status":"started","day":1,"phase":"huddle","you":{"id":"d","name":"Inspecteur","team":"detective","ready":true,"isHost":false},"players":[],"chat":[],"briefing":"HAVENKADE 12, 03:02. Brand in een loods."}
        """.trimIndent()
        val view = json.decodeFromString<SessionView>(raw)
        assertEquals("detective", view.you?.team)
        assertTrue(view.chat.isEmpty())
        assertTrue("SCH-14-X" !in (view.briefing ?: ""))
        assertTrue("Van Dorp" !in (view.briefing ?: ""))
    }
}
