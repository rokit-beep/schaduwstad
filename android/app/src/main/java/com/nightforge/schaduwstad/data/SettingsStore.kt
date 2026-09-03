package com.nightforge.schaduwstad.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.nightforge.schaduwstad.network.ConnectionConfig
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore("schaduwstad")

class SettingsStore(private val context: Context) {
    private val hostKey = stringPreferencesKey("server_host")
    private val portKey = intPreferencesKey("server_port")
    private val nameKey = stringPreferencesKey("player_name")

    val host: Flow<String> = context.dataStore.data.map { it[hostKey] ?: ConnectionConfig.DEFAULT_HOST }
    val port: Flow<Int> = context.dataStore.data.map { it[portKey] ?: ConnectionConfig.DEFAULT_PORT }
    val playerName: Flow<String> = context.dataStore.data.map { it[nameKey] ?: "" }

    suspend fun setHost(value: String) { context.dataStore.edit { it[hostKey] = value.trim() } }
    suspend fun setPort(value: Int) { context.dataStore.edit { it[portKey] = value } }
    suspend fun setPlayerName(value: String) { context.dataStore.edit { it[nameKey] = value.trim() } }
}
