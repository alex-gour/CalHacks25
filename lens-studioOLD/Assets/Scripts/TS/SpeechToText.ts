/** @format */

@component
export class SpeechToText extends BaseScriptComponent {
	@input()
	text: Text
	// Remote service module for fetching data
	private voiceMLModule: VoiceMLModule

	onAwake() {
		try {
			// Try to load the VoiceML module
			this.voiceMLModule = require('LensStudio:VoiceMLModule')
		} catch (error) {
			print('Warning: VoiceMLModule not available: ' + error)
			return
		}

		try {
			if (!this.text) {
				print('SpeechToText: Text component not assigned')
				return
			}

			let options = VoiceML.ListeningOptions.create()
			options.shouldReturnAsrTranscription = true
			options.shouldReturnInterimAsrTranscription = true
			this.voiceMLModule.onListeningEnabled.add(() => {
				this.voiceMLModule.startListening(options)
				this.voiceMLModule.onListeningUpdate.add(this.onListenUpdate)
			})
		} catch (error) {
			print('SpeechToText initialization error: ' + error)
		}
	}

	onListenUpdate = (eventData: VoiceML.ListeningUpdateEventArgs) => {
		if (eventData.isFinalTranscription) {
			this.text.text = eventData.transcription
		}
	}
}
