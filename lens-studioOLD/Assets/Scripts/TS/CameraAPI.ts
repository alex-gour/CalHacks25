/** @format */

@component
export class ContinuousCameraFrameExample extends BaseScriptComponent {
	private cameraModule: CameraModule
	private cameraRequest: CameraModule.CameraRequest
	private cameraTexture: Texture
	private cameraTextureProvider: CameraTextureProvider

	@input
	@hint('The image in the scene that will be showing the captured frame.')
	uiImage: Image | undefined

	onAwake() {
		try {
			// Try to load the Camera module
			this.cameraModule = require('LensStudio:CameraModule')
		} catch (error) {
			print('Warning: CameraModule not available: ' + error)
			return
		}

		try {
			this.createEvent('OnStartEvent').bind(() => {
				try {
					this.cameraRequest = CameraModule.createCameraRequest()
					this.cameraRequest.cameraId = CameraModule.CameraId.Default_Color

					this.cameraTexture = this.cameraModule.requestCamera(
						this.cameraRequest
					)
					this.cameraTextureProvider = this.cameraTexture
						.control as CameraTextureProvider

					this.cameraTextureProvider.onNewFrame.add((cameraFrame) => {
						if (this.uiImage) {
							this.uiImage.mainPass.baseTex = this.cameraTexture
						}
					})
				} catch (error) {
					print('CameraAPI initialization error: ' + error)
				}
			})
		} catch (error) {
			print('CameraAPI onAwake error: ' + error)
		}
	}
}
