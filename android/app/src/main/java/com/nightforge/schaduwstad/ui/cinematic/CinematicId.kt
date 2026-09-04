package com.nightforge.schaduwstad.ui.cinematic

import android.content.Context

enum class CinematicId(val wire: String, val raw: String, val thumb: String) {
    CAMERA_ANALYSIS("camera_analysis", "cin_d01_camera_analysis", "thumb_d01_camera_analysis"),
    EVIDENCE_INSPECTION("evidence_inspection", "cin_d02_evidence_inspection", "thumb_d02_evidence_inspection"),
    LICENSE_PLATE("license_plate", "cin_d03_license_plate", "thumb_d03_license_plate"),
    TIRE_TRACKS("tire_tracks", "cin_d04_tire_tracks", "thumb_d04_tire_tracks"),
    WITNESS("witness", "cin_d05_witness", "thumb_d05_witness"),
    CONTAINER_RECORDS("container_records", "cin_d06_container_records", "thumb_d06_container_records"),
    MOVE_VEHICLE("move_vehicle", "cin_m01_move_vehicle", "thumb_m01_move_vehicle"),
    CAMERA_SABOTAGE("camera_sabotage", "cin_m02_camera_sabotage", "thumb_m02_camera_sabotage"),
    MOVE_EVIDENCE("move_evidence", "cin_m03_move_evidence", "thumb_m03_move_evidence"),
    WARN_CONTACT("warn_contact", "cin_m04_warn_contact", "thumb_m04_warn_contact"),
    FALSE_ALIBI("false_alibi", "cin_m05_false_alibi", "thumb_m05_false_alibi"),
    PRESSURE_WITNESS("pressure_witness", "cin_m06_pressure_witness", "thumb_m06_pressure_witness"),
    CAMERA_CONFLICT("camera_conflict", "cin_camera_conflict", "thumb_camera_conflict"),
    CONFLICT("conflict", "cin_conflict", "thumb_conflict"),
    WITNESS_CONFLICT("witness_conflict", "cin_witness_conflict", "thumb_witness_conflict"),
    VEHICLE_CONFLICT("vehicle_conflict", "cin_vehicle_conflict", "thumb_vehicle_conflict"),
    CLUE_LICENSE_PLATE("clue_kenteken", "cin_clue_kenteken", "thumb_clue_kenteken"),
    CLUE_LEDGER("clue_kasboek", "cin_clue_kasboek", "thumb_clue_kasboek"),
    CLUE_TIRE("clue_bandenspoor", "cin_clue_bandenspoor", "thumb_clue_bandenspoor"),
    CLUE_SOOT("clue_roetmap", "cin_clue_roetmap", "thumb_clue_roetmap"),
    EI01("enemy_ei01_cameras_offline", "cin_ei01_cameras_offline", "thumb_ei01_cameras_offline"),
    EI02("enemy_ei02_witness_retracts", "cin_ei02_witness_retracts", "thumb_ei02_witness_retracts"),
    EI03("enemy_ei03_witness_missing", "cin_ei03_witness_missing", "thumb_ei03_witness_missing"),
    EI04("enemy_ei04_evidence_moved", "cin_ei04_evidence_moved", "thumb_ei04_evidence_moved"),
    EI05("enemy_ei05_unexpected_new_trail", "cin_ei05_unexpected_new_trail", "thumb_ei05_unexpected_new_trail"),
    EI06("enemy_ei06_mafia_notices_surveillance", "cin_ei06_mafia_notices_surveillance", "thumb_ei06_mafia_notices_surveillance"),
    EI07("enemy_ei07_location_compromised", "cin_ei07_location_compromised", "thumb_ei07_location_compromised"),
    EI08("enemy_ei08_vehicle_followed", "cin_ei08_vehicle_followed", "thumb_ei08_vehicle_followed"),
    EI09("enemy_ei09_comms_leaked", "cin_ei09_comms_leaked", "thumb_ei09_comms_leaked"),
    EI10("enemy_ei10_investigation_stalled", "cin_ei10_investigation_stalled", "thumb_ei10_investigation_stalled"),
    ;

    fun rawRes(context: Context): Int =
        context.resources.getIdentifier(raw, "raw", context.packageName)

    fun thumbRes(context: Context): Int =
        context.resources.getIdentifier(thumb, "drawable", context.packageName)

    companion object {
        fun fromWire(id: String?): CinematicId? {
            if (id.isNullOrBlank()) return null
            return entries.find { it.wire == id || it.name.equals(id, ignoreCase = true) }
        }
    }
}
