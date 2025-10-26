/** @format */

//@input SceneObject menuBackground
//@input SceneObject menuText
//@input SceneObject yesButton
//@input SceneObject noButton

// Hide menu initially
script.menuBackground.enabled = false
script.menuText.enabled = false
script.yesButton.enabled = false
script.noButton.enabled = false

// Listen for snap image capture event
var event = script.createEvent('SnapImageCaptureEvent')
event.bind(function () {
	script.menuBackground.enabled = true
	script.menuText.enabled = true
	script.yesButton.enabled = true
	script.noButton.enabled = true
})

// Add touch events for buttons
function addButtonTouch(button, callback) {
	var touchComponent = button.getComponent('Component.TouchComponent')
	if (!touchComponent) {
		touchComponent = button.createComponent('Component.TouchComponent')
	}
	touchComponent.onTouchStart.add(callback)
}

addButtonTouch(script.yesButton, function () {
	print('YES pressed')
	// TODO: Open Amazon link here after API integration
	script.menuBackground.enabled = false
	script.menuText.enabled = false
	script.yesButton.enabled = false
	script.noButton.enabled = false
})

addButtonTouch(script.noButton, function () {
	print('NO pressed')
	script.menuBackground.enabled = false
	script.menuText.enabled = false
	script.yesButton.enabled = false
	script.noButton.enabled = false
})

// Set menu text
var textComponent = script.menuText.getComponent('Component.Text')
if (textComponent) {
	textComponent.text = 'Would you like to buy this item on Amazon?'
}
