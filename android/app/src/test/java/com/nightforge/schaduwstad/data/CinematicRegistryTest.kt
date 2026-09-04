package com.nightforge.schaduwstad.data

import com.nightforge.schaduwstad.ui.cinematic.CinematicCatalog
import com.nightforge.schaduwstad.ui.cinematic.CinematicId
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class CinematicRegistryTest {
    @Test
    fun everyDay1ServerWireIdResolves() {
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
        assertNull(CinematicId.fromWire("snitch"))
        assertTrue(CinematicId.entries.size >= 20)
    }

    @Test
    fun futureLibraryIdsAreRecognizedWithoutGameplay() {
        assertTrue(CinematicCatalog.knows("d2_d01_container_inspection"))
        assertTrue(CinematicCatalog.knows("d5_c04_suspect_escapes"))
        assertTrue(CinematicCatalog.knows("global_g07_witness_secured"))
        assertTrue(CinematicCatalog.knows("enemy_ei03_witness_missing"))
        assertTrue(CinematicCatalog.knows("camera_analysis"))
        assertFalse(CinematicCatalog.knows("snitch"))
        assertNotNull(CinematicId.fromWire("enemy_ei01_cameras_offline"))
    }

    @Test
    fun dayResultParsesCinematicsWithoutLeakingUnknownKeys() {
        val json = kotlinx.serialization.json.Json { ignoreUnknownKeys = true }
        val raw = """
            {"headline":"Vier seconden beeld.","cinematics":[{"id":"camera_conflict","title":"x","kind":"contested","team":null}],"clues":{"kenteken":{"id":"kenteken","name":"Kentekenfragment","status":"disputed"}},"followUps":[{"id":"check_worker","label":"Medewerker controleren","team":"detective"}],"evidenceOld":18,"heatOld":28}
        """.trimIndent()
        val result = json.decodeFromString<DayResult>(raw)
        assertEquals("camera_conflict", result.cinematics.first().id)
        assertEquals("kenteken", result.clues["kenteken"]?.id)
        assertEquals("check_worker", result.followUps.first().id)
        assertEquals(18, result.evidenceOld)
    }
}
