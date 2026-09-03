package com.nightforge.schaduwstad.network

data class ConnectionConfig(val address: String, val port: Int = 8098) {
    init { require(port in 1..65535) }

    val host: String
        get() = address.trim()
            .removePrefix("http://").removePrefix("https://")
            .removePrefix("ws://").removePrefix("wss://")
            .substringBefore('/').substringBefore(':')

    fun httpBaseUrl(): String = "http://$host:$port"
    fun webSocketUrl(lobbyCode: String, token: String): String =
        "ws://$host:$port/games/schaduwstad/ws/${lobbyCode.uppercase()}?token=$token"

    fun isUsable(): Boolean = host.isNotBlank() && host.none(Char::isWhitespace)

    companion object {
        const val DEFAULT_HOST = "100.103.203.62"
        const val DEFAULT_PORT = 8098
    }
}
