package com.studentsyncsa.studentsyncsa.accessibility

import android.view.KeyEvent

object InputSimulator {

    fun typeText(text: String): Boolean = try {
        val safe = text
            .replace("\\", "\\\\\\\\")
            .replace("'", "\\\\'")
            .replace("\"", "\\\\\"")
            .replace(" ", "%s")
            .replace("\n", " ")
        val proc = Runtime.getRuntime().exec("input text \"$safe\"")
        proc.waitFor()
        proc.exitValue() == 0
    } catch (_: Exception) { false }

    fun pressEnter(): Boolean = pressKey(KeyEvent.KEYCODE_ENTER)

    fun pressTab(): Boolean = pressKey(KeyEvent.KEYCODE_TAB)

    fun pressBack(): Boolean = pressKey(KeyEvent.KEYCODE_BACK)

    fun pressDone(): Boolean = pressKey(KeyEvent.KEYCODE_DPAD_DOWN)

    fun pressNext(): Boolean = pressKey(KeyEvent.KEYCODE_NUMPAD_ENTER)

    private fun pressKey(code: Int): Boolean = try {
        val proc = Runtime.getRuntime().exec("input keyevent $code")
        proc.waitFor()
        proc.exitValue() == 0
    } catch (_: Exception) { false }

    fun clearField(): Boolean = try {
        val proc = Runtime.getRuntime().exec("input keyevent KEYCODE_MOVE_END")
        proc.waitFor()
        // Select all backspace
        val sel = Runtime.getRuntime().exec("input keyevent --longpress KEYCODE_DEL")
        sel.waitFor()
        sel.exitValue() == 0
    } catch (_: Exception) { false }
}
