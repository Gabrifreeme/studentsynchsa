package com.studentsyncsa.studentsyncsa.accessibility

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.os.Bundle
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import java.util.ArrayDeque

class AutofillAccessibilityService : AccessibilityService() {

    companion object {
        private var instance: AutofillAccessibilityService? = null
        fun getInstance() = instance
        fun isRunning() = instance != null
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        serviceInfo = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityEvent.TYPE_VIEW_FOCUSED or
                    AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED or
                    AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
            notificationTimeout = 100
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}
    override fun onInterrupt() {}

    override fun onDestroy() {
        instance = null
        super.onDestroy()
    }

    fun scanFields(): List<Map<String, String>> {
        val fields = mutableListOf<Map<String, String>>()
        val root = rootInActiveWindow ?: return fields
        scanNode(root, fields)
        return fields
    }

    private fun scanNode(node: AccessibilityNodeInfo, result: MutableList<Map<String, String>>) {
        val cn = node.className?.toString() ?: ""
        val isEditable = node.isEditable
        val isClickable = node.isClickable && (cn.contains("Button", ignoreCase = true) || cn.contains("Switch", ignoreCase = true))

        if (isEditable || isClickable) {
            result.add(mapOf(
                "className" to cn,
                "text" to (node.text?.toString() ?: ""),
                "hint" to (node.hintText?.toString() ?: ""),
                "contentDescription" to (node.contentDescription?.toString() ?: ""),
                "viewId" to (node.viewIdResourceName ?: ""),
                "isEditable" to isEditable.toString(),
                "isFocused" to node.isFocused.toString()
            ))
        }

        for (i in 0 until node.childCount) {
            node.getChild(i)?.let { child ->
                scanNode(child, result)
                child.recycle()
            }
        }
    }

    fun fillFocused(text: String): Boolean {
        val root = rootInActiveWindow ?: return false
        val focused = root.findFocus(AccessibilityNodeInfo.FOCUS_INPUT)
        root.recycle()
        if (focused != null && focused.isEditable) {
            return setTextAndRecycle(focused, text)
        }
        focused?.recycle()
        return false
    }

    fun fillField(keyword: String, value: String): Boolean {
        val root = rootInActiveWindow ?: return false
        val node = findEditableNode(root, keyword.lowercase())
        if (node != null) {
            val ok = setTextAndRecycle(node, value)
            root.recycle()
            return ok
        }
        root.recycle()
        return false
    }

    fun fillAll(fields: List<Map<String, String>>): Map<String, Boolean> {
        val results = mutableMapOf<String, Boolean>()
        val root = rootInActiveWindow ?: return results

        for (entry in fields) {
            val keyword = (entry["keyword"] ?: "").lowercase()
            val value = entry["value"] ?: ""
            val name = entry["name"] ?: keyword
            if (value.isEmpty()) continue

            val node = findEditableNode(root, keyword)
            if (node != null) {
                results[name] = setTextKeepNode(node, value)
            } else {
                results[name] = false
            }
        }
        root.recycle()
        return results
    }

    private fun findEditableNode(root: AccessibilityNodeInfo, query: String): AccessibilityNodeInfo? {
        var best: Pair<AccessibilityNodeInfo, Int>? = null
        val queue = ArrayDeque<AccessibilityNodeInfo>().apply { add(root) }

        while (queue.isNotEmpty()) {
            val node = queue.removeFirst() ?: continue
            if (!node.isEditable) {
                for (i in 0 until node.childCount) {
                    node.getChild(i)?.let { queue.add(it) }
                }
                continue
            }

            var score = 0
            val hint = (node.hintText?.toString() ?: "").lowercase()
            val desc = (node.contentDescription?.toString() ?: "").lowercase()
            val viewId = (node.viewIdResourceName ?: "").lowercase()
            val text = (node.text?.toString() ?: "").lowercase()

            if (viewId.contains(query)) score += 20
            if (desc.contains(query)) score += 15
            if (hint.contains(query)) score += 10
            if (text.contains(query)) score += 5

            if (score > 0 && (best == null || score > best.second)) {
                best = Pair(node, score)
            }

            for (i in 0 until node.childCount) {
                node.getChild(i)?.let { queue.add(it) }
            }
        }
        return best?.first
    }

    private fun setTextAndRecycle(node: AccessibilityNodeInfo, text: String): Boolean {
        val args = Bundle().apply {
            putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text)
        }
        val ok = node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
        node.recycle()
        return ok
    }

    private fun setTextKeepNode(node: AccessibilityNodeInfo, text: String): Boolean {
        val args = Bundle().apply {
            putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text)
        }
        return node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
    }
}
