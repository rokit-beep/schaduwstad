package com.nightforge.schaduwstad.ui.cinematic

import android.content.Context
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
data class ManifestFile(val assets: List<ManifestAsset> = emptyList())

@Serializable
data class ManifestAsset(
    @SerialName("cinematic_id") val cinematicId: String,
    val day: String? = null,
    val faction: String? = null,
    val category: String? = null,
    val visibility: String? = null,
    val action: String? = null,
)

data class CatalogEntry(
    val id: String,
    val raw: String? = null,
    val thumb: String? = null,
    val day: String? = null,
    val visibility: String? = null,
    val title: String? = null,
    val bundled: Boolean = false,
)

object CinematicCatalog {
    private val json = Json { ignoreUnknownKeys = true }
    @Volatile private var extras: Map<String, CatalogEntry> = emptyMap()
    @Volatile private var loaded = false

    fun load(context: Context) {
        if (loaded) return
        synchronized(this) {
            if (loaded) return
            extras = runCatching {
                context.assets.open("cinematics/manifest.json").bufferedReader().use { it.readText() }
                    .let { json.decodeFromString<ManifestFile>(it) }
                    .assets
                    .associate { asset ->
                        asset.cinematicId to CatalogEntry(
                            id = asset.cinematicId,
                            day = asset.day,
                            visibility = asset.visibility,
                            title = asset.action,
                            bundled = false,
                        )
                    }
            }.getOrElse { emptyMap() }
            loaded = true
        }
    }

    fun knows(id: String?): Boolean {
        if (id.isNullOrBlank()) return false
        if (CinematicId.fromWire(id) != null) return true
        if (extras.containsKey(id)) return true
        return FUTURE.contains(id)
    }

    fun resolve(context: Context, id: String?): CatalogEntry? {
        load(context)
        if (id.isNullOrBlank()) return null
        CinematicId.fromWire(id)?.let { cin ->
            return CatalogEntry(cin.wire, cin.raw, cin.thumb, bundled = true, title = cin.wire)
        }
        extras[id]?.let { return it }
        if (FUTURE.contains(id)) return CatalogEntry(id = id)
        return null
    }

    fun rawRes(context: Context, id: String?): Int {
        val entry = resolve(context, id) ?: return 0
        val name = entry.raw ?: return 0
        return context.resources.getIdentifier(name, "raw", context.packageName)
    }

    fun thumbRes(context: Context, id: String?): Int {
        val entry = resolve(context, id) ?: return 0
        val name = entry.thumb ?: return 0
        return context.resources.getIdentifier(name, "drawable", context.packageName)
    }

    val FUTURE: Set<String> = setOf(
        "d2_d01_container_inspection", "d2_d02_customs_records", "d2_d03_gps_tracker",
        "d2_d04_harbor_worker", "d2_d05_truck_route", "d2_d06_hidden_compartment",
        "d2_m01_move_container", "d2_m02_destroy_gps", "d2_m03_customs_bribe",
        "d2_m04_swap_truck", "d2_m05_fake_papers", "d2_m06_leave_bait_container",
        "d2_c01_container_intercepted", "d2_c02_gps_signal_lost", "d2_c03_simultaneous_arrival",
        "d2_c04_hidden_cargo_nearly_found", "d2_r01_fake_freight_bill", "d2_r02_gps_module",
        "d2_r03_customs_seal", "d2_r04_hidden_phone",
        "d3_d01_anonymous_tip", "d3_d02_phone_metadata", "d3_d03_secret_meeting_observe",
        "d3_d04_money_flows", "d3_d05_meet_informant", "d3_d06_communication_patterns",
        "d3_m01_check_internal_phones", "d3_m02_observe_suspect_member", "d3_m03_spread_false_info",
        "d3_m04_loyalty_test", "d3_m05_replace_channel", "d3_m06_confront_possible_traitor",
        "d3_c01_secret_meeting_conflict", "d3_c02_false_tip_reaches_police", "d3_c03_informant_escapes",
        "d3_c04_internal_suspicion_explodes", "d3_r01_burner_phone", "d3_r02_unexplained_payment",
        "d3_r03_leaked_location", "d3_r04_coded_message",
        "d4_d01_bank_transactions", "d4_d02_observe_office", "d4_d03_inspect_books",
        "d4_d04_follow_account", "d4_d05_follow_cash_transport", "d4_d06_reconstruct_structure",
        "d4_m01_move_cash", "d4_m02_destroy_books", "d4_m03_warn_strawman",
        "d4_m04_open_new_account", "d4_m05_change_cash_transport", "d4_m06_front_business",
        "d4_c01_cash_transport_intercepted", "d4_c02_empty_office_raid", "d4_c03_digital_transfer_blocked",
        "d4_c04_financial_trail_opens", "d4_r01_cash_ledger", "d4_r02_bank_transfer",
        "d4_r03_shell_company_document", "d4_r04_cash_bundle",
        "d5_d01_position_observation", "d5_d02_prepare_arrest_team", "d5_d03_track_phone_locations",
        "d5_d04_finalize_evidence", "d5_d05_shadow_suspect", "d5_d06_prepare_raid",
        "d5_m01_leave_safehouse", "d5_m02_destroy_phones", "d5_m03_change_route",
        "d5_m04_destroy_evidence", "d5_m05_hide_person", "d5_m06_counter_surveillance",
        "d5_c01_chase", "d5_c02_failed_arrest", "d5_c03_safehouse_raid", "d5_c04_suspect_escapes",
        "global_g01_evidence_increased", "global_g02_evidence_destroyed", "global_g03_heat_increased",
        "global_g04_heat_decreased", "global_g05_new_anonymous_tip", "global_g06_witness_disappeared",
        "global_g07_witness_secured", "global_g08_police_surveillance", "global_g09_mafia_surveillance",
        "global_g10_unknown_vehicle", "global_g11_phone_signal_detected", "global_g12_phone_destroyed",
        "global_g13_police_raid", "global_g14_mafia_location_compromised", "global_g15_operation_successful",
        "global_g16_operation_partially_failed", "global_g17_critical_clue_discovered",
        "global_g18_false_lead_discovered", "global_g19_team_under_pressure", "global_g20_night_transition",
        "enemy_ei01_cameras_offline", "enemy_ei02_witness_retracts", "enemy_ei03_witness_missing",
        "enemy_ei04_evidence_moved", "enemy_ei05_unexpected_new_trail", "enemy_ei06_mafia_notices_surveillance",
        "enemy_ei07_location_compromised", "enemy_ei08_vehicle_followed", "enemy_ei09_comms_leaked",
        "enemy_ei10_investigation_stalled",
    )
}
