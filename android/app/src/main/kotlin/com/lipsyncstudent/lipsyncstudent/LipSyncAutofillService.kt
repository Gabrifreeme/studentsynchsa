/* TEMPORARILY DISABLED — autofill service blocked build. Re-enable tonight. */
/* package com.lipsyncstudent.lipsyncstudent
import android.app.assist.AssistStructure
import android.os.CancellationSignal
import android.service.autofill.AutofillService
import android.service.autofill.Dataset
import android.service.autofill.FillCallback
import android.service.autofill.FillResponse
import android.service.autofill.SaveCallback
import android.service.autofill.SaveRequest
import android.view.autofill.AutofillValue
import android.service.autofill.FillRequest
import android.content.SharedPreferences

class LipSyncAutofillService : AutofillService() {
    override fun onFillRequest(request: FillRequest, cancellationSignal: CancellationSignal, callback: FillCallback) {
        val prefs = getSharedPreferences("autofill_profile", MODE_PRIVATE)
        val response = FillResponse.Builder()
        val dataset = Dataset.Builder()
        val value = AutofillValue.forList(prefs.getString("surname", ""))
        dataset.setValue(value)
        response.addDataset(dataset.build())
        callback.onSuccess(response.build())
    }
    override fun onSaveRequest(request: SaveRequest, callback: SaveCallback) {
        callback.onSuccess()
    }
    override fun onCreate() {
        super.onCreate()
    }
}
*/
