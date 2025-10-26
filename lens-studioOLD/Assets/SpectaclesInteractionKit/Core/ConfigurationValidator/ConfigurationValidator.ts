/** @format */

const TAG = 'ConfigurationValidator'
const SIK_VERSION = '0.10.0'

/**
 * This class is responsible for validating the configuration settings for running the Spectacles Interaction Kit (SIK) in Lens Studio.
 *
 */
@component
export class ConfigurationValidator extends BaseScriptComponent {
	onAwake(): void {
		// Only validate in editor mode, not on actual Spectacles devices
		if (global.deviceInfoSystem.isEditor()) {
			if (!global.deviceInfoSystem.isSpectacles()) {
				print(
					"Warning: To run Spectacles Interaction Kit in the Lens Studio Preview, set the Preview Panel's Device Type Override to Spectacles, or the Simulation Mode to Spectacles (2024)!"
				)
				// Don't throw error, just warn
			}
		}

		print('SIK Version : ' + SIK_VERSION)
	}
}
