package com.nightforge.schaduwstad.data

import com.nightforge.schaduwstad.ui.cinematic.CinematicId
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class CinematicRegistryTest {
    @Test
    fun everyServerWireIdResolves() {
        val ids = listOf(
            "camera_analysis", "evidence_inspection", "license_plate", "tire_tracks",
            "witness", "container_records", "move_vehicle", "camera_sabotage",
            "move_evidence", "warn_contact", "false_alibi", "pressure_witness",
            "camera_conflict", "conflict", "witness_conflict", "vehicle_conflict",
            "clue_kenteken", "clue_kasboek", "clue_bandenspoor", "clue_roetmap",
        )
        ids.forEach { wire ->
            val cinematic = CinematicId.fromWire(wire)
            assertNotNull(wire, cinematic)
            assertEquals(wire, cinematic!!.wire)
        }
        assertEquals(20, CinematicId.entries.size)
        assertNull(CinematicId.fromWire("snitch"))
    }

    @Test
    fun dayResultParsesCinematicsWithoutLeakingUnknownKeys() {
        val json = kotlinx.serialization.json.Json { ignoreUnknownKeys = true }
        val raw = """
            {"headline":"Vier seconden beeld.","cinematics":[{"id":"camera_conflict","title":"x","kind":"contested","team":null}],"clues":{"kenteken":{"id":"kenteken","name":"Kentekenfragment","status":"disputed"}}}
        """.trimIndent()
        val result = json.decodeFromString<DayResult>(raw)
        assertEquals("camera_conflict", result.cinematics.first().id)
        assertEquals("kenteken", result.clues["kenteken"]?.id)
    }
}
