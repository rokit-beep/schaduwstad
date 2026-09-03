package com.nightforge.schaduwstad.network

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ConnectionConfigTest {
    @Test
    fun stripsSchemesAndBuildsNamespacedSocket() {
        val cfg = ConnectionConfig("http://100.103.203.62:8098", 8098)
        assertEquals("100.103.203.62", cfg.host)
        assertEquals("http://100.103.203.62:8098", cfg.httpBaseUrl())
        assertEquals(
            "ws://100.103.203.62:8098/games/schaduwstad/ws/AB12?token=tok",
            cfg.webSocketUrl("ab12", "tok"),
        )
        assertTrue(cfg.isUsable())
        assertFalse(ConnectionConfig(" ").isUsable())
    }
}
