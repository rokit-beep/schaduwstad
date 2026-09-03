package com.nightforge.schaduwstad.network

class ApiException(
    val code: String,
    override val message: String,
    val httpStatus: Int? = null,
) : Exception(message)
