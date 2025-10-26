/** @format */

import {Interactable} from '../../SpectaclesInteractionKit/Components/Interaction/Interactable/Interactable'
import {InteractorEvent} from '../../SpectaclesInteractionKit/Core/Interactor/InteractorEvent'
import {SIK} from '../../SpectaclesInteractionKit/SIK'
import {TextToSpeechOpenAI} from './TextToSpeechOpenAI'
import {HttpFetchModule} from './utils/HttpClient'

// Add location module requirement
try {
	require('LensStudio:RawLocationModule')
} catch (error) {
	print('Warning: RawLocationModule not available: ' + error)
}

type SnapPurchaseProduct = {
	detected_label?: string
	matched_product?: {
		id: string
		name: string
		category: string
		shopify_url: string
		[key: string]: unknown
	} | null
	confidence?: number
	match_reason?: string
}

type SnapPurchaseResult = {
	detected_products: Array<{
		label: string
		percent_full?: number
		is_low?: boolean
		confidence?: number
		box_2d?: number[]
	}>
	search_results?: Array<{
		title?: string
		url?: string
		snippet?: string
	}>
	catalog_match?: SnapPurchaseProduct | null
	purchase_url?: string | null
	purchase_result?: {
		success?: boolean
		message?: string
		product_url?: string
		cart_url?: string
		[key: string]: unknown
	} | null
}


@component
export class VisionOpenAI extends BaseScriptComponent {
	@input textInput: Text
	@input textOutput: Text
	@input image: Image
	@input interactable: Interactable
	@input ttsComponent: TextToSpeechOpenAI
	@input LLM_analyse: Text

	// Chat history display
	@input chatHistoryText: Text // Reference to popup1 text element
	@input maxHistoryLength: number = 10 // Maximum number of conversation pairs to store

	// Claude summary
	@input enableSummary: boolean = true // Option to enable/disable summaries

	// Maximum characters per line for proper text wrapping
	@input maxCharsPerLine: number = 100

	// Location properties
	latitude: number
	longitude: number
	private locationService: LocationService
	private updateLocationEvent: DelayedCallbackEvent

	// Chat history storage
	private chatHistory: string[] = []

	@input('string')
	backendBaseUrl: string = 'https://resorbent-alanna-semimoderately.ngrok-free.dev'

	private fetchModule: HttpFetchModule | null = null

	private isProcessing: boolean = false

	private resolvedBaseUrl: string | null = null

	// Hard-coded Snap & Buy behaviour: always auto-purchase using catalog data
	private readonly snapPurchaseOptions = {
		autoPurchase: true,
		useCatalog: true,
		quantity: '1',
	} as const

	onAwake() {
		try {
			this.createEvent('OnStartEvent').bind(() => {
				this.onStart()
			})

			// Initialize location update event
			this.updateLocationEvent = this.createEvent('DelayedCallbackEvent')
			this.updateLocationEvent.bind(() => {
				this.updateLocation()
			})
		} catch (error) {
			print('Error in VisionOpenAI onAwake: ' + error)
		}
	}

	private getBackendUrl(): string {
		if (this.resolvedBaseUrl) {
			return this.resolvedBaseUrl
		}

		let candidate = (this.backendBaseUrl || '').trim()
		if (!candidate) {
			candidate = 'https://resorbent-alanna-semimoderately.ngrok-free.dev'
		}

		if (!candidate.startsWith('http')) {
			candidate = 'https://' + candidate
		}

		if (candidate.startsWith('http://')) {
			print('Upgrading backendBaseUrl to https for ngrok usage')
			candidate = 'https://' + candidate.substring(7)
		}

		if (candidate.endsWith('/')) {
			candidate = candidate.substring(0, candidate.length - 1)
		}

		this.resolvedBaseUrl = candidate
		return this.resolvedBaseUrl
	}

	private ensureFetchModule(): HttpFetchModule {
		if (this.fetchModule) {
			return this.fetchModule
		}

		try {
			this.fetchModule = require('LensStudio:InternetModule') as HttpFetchModule
		} catch (internetError) {
			print('InternetModule not available, trying RemoteServiceModule: ' + internetError)
			this.fetchModule = require('LensStudio:RemoteServiceModule') as HttpFetchModule
		}

		if (!this.fetchModule) {
			throw new Error('No fetch-capable module available. Please add an Internet Module to the project.')
		}

		return this.fetchModule
	}

	onStart() {
		try {
			//let interactionManager = SIK.InteractionManager

			// Define the desired callback logic for the relevant Interactable event.
			let onTriggerEndCallback = (event: InteractorEvent) => {
				this.handleTriggerEnd(event)
			}

			if (this.interactable) {
				this.interactable.onInteractorTriggerEnd(onTriggerEndCallback)
			} else {
				print('Warning: Interactable component not assigned')
			}

			const backendUrl = this.getBackendUrl()
			if (!backendUrl) {
				print(
					'Backend base URL is not configured. Set backendBaseUrl on the component.'
				)
			}

			this.ensureFetchModule()

			// Initialize location service
			this.initLocationService()

			// Initialize chat history display
			this.updateChatHistoryDisplay()
		} catch (error) {
			print('Error in VisionOpenAI onStart: ' + error)
		}
	}

	// Utility function to make text wrap within a textbox
	makeTextWrappable(text: string): string {
		if (!text) return ''

		// Split by existing newlines first
		const paragraphs = text.split('\n')
		let result = []

		for (const paragraph of paragraphs) {
			if (paragraph.length <= this.maxCharsPerLine) {
				result.push(paragraph)
				continue
			}

			// Break long paragraphs into wrapped lines
			let remainingText = paragraph
			while (remainingText.length > 0) {
				// If remaining text is shorter than max length, just add it
				if (remainingText.length <= this.maxCharsPerLine) {
					result.push(remainingText)
					break
				}

				// Find the last space within the max line length
				let cutPoint = remainingText.lastIndexOf(' ', this.maxCharsPerLine)
				if (cutPoint === -1 || cutPoint === 0) {
					// No appropriate space found, force cut at max length
					cutPoint = this.maxCharsPerLine
				}

				result.push(remainingText.substring(0, cutPoint))
				remainingText = remainingText.substring(cutPoint + 1) // +1 to skip the space
			}
		}

		return result.join('\n')
	}

	// Add a new conversation to the chat history
	addToHistory(userQuery: string, response: string) {
		// Create a formatted conversation entry
		const historyEntry = `User: ${userQuery}\nSnapAid: ${response}\n`

		// Add to the history array
		this.chatHistory.push(historyEntry)

		// If we exceed the maximum history length, remove the oldest entries
		if (this.chatHistory.length > this.maxHistoryLength) {
			this.chatHistory = this.chatHistory.slice(
				this.chatHistory.length - this.maxHistoryLength
			)
		}

		// Update the history display
		this.updateChatHistoryDisplay()
	}

	private formatSnapAndBuyResponse(result: SnapPurchaseResult | null): string {
		if (!result) {
			return 'No response received from Snap & Buy backend.'
		}

		const lines: string[] = []

		if (result.detected_products && result.detected_products.length > 0) {
			const topProduct = result.detected_products[0]
			lines.push(`Detected: ${topProduct.label || 'unknown product'}`)
			if (topProduct.percent_full !== undefined) {
				lines.push(
					`Fill level: ${Math.round(topProduct.percent_full)}% (${topProduct.is_low ? 'low' : 'ok'})`
				)
			}
		} else {
			lines.push('No products detected in the scene.')
		}

		if (result.catalog_match) {
			const match = result.catalog_match
			if (match.matched_product) {
				lines.push(
					`Catalog match: ${match.matched_product.name} (confidence ${Math.round(
						(match.confidence || 0) * 100
					)}%)`
				)
				lines.push(`Shopify URL: ${match.matched_product.shopify_url}`)
			} else if (match.match_reason) {
				lines.push(`Catalog attempt failed: ${match.match_reason}`)
			}
		}

		if (result.search_results && result.search_results.length > 0) {
			const bestSearch = result.search_results[0]
			lines.push(`Top search result: ${bestSearch.title || bestSearch.url}`)
			if (bestSearch.url) {
				lines.push(`URL: ${bestSearch.url}`)
			}
		}

		if (result.purchase_url) {
			lines.push(`Purchase URL: ${result.purchase_url}`)
		}

		if (result.purchase_result) {
			const purchase = result.purchase_result
			const status = purchase.success ? '✅ Purchase initiated' : '⚠️ Purchase not completed'
			lines.push(status)
			if (purchase.message) {
				lines.push(`Details: ${purchase.message}`)
			}
			if (purchase.cart_url) {
				lines.push(`Cart: ${purchase.cart_url}`)
			}
		}

		if (lines.length === 0) {
			lines.push('Snap & Buy response contained no actionable data.')
		}

		return lines.join('\n')
	}

	// Update the chat history display in the popup1 text element
	updateChatHistoryDisplay() {
		if (!this.chatHistoryText) {
			print('Chat history text element not assigned')
			return
		}

		// Join all history entries and make them wrappable
		const fullHistory = this.chatHistory.join('\n')
		this.chatHistoryText.text = this.makeTextWrappable(fullHistory)
	}

	// Get the full chat history as a single string (for including in prompts)
	getChatHistoryString(): string {
		return this.chatHistory.join('\n')
	}

	// Generate summary with Claude API and add to response
	async generateBulletSummary(
		responseText: string
	): Promise<{fullText: string; summaryOnly: string}> {
		if (!this.enableSummary) {
			print('Summary generation disabled')
			return {
				fullText: responseText,
				summaryOnly: '',
			}
		}

		try {
			print('Generating bullet-point summary with Claude...')

			const prompt = `List the key points from this response in 3-5 concise bullet points.\n${responseText}`

			const backendUrl = this.getBackendUrl()

			const fetchModule = this.ensureFetchModule()

			const request = new Request(`${backendUrl}/api/summarize`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({summaryPrompt: prompt}),
			})

			const response = await fetchModule.fetch(request)

			if (response.status === 200) {
				const responseData = await response.json()
				const summaryText = (responseData && responseData.summary) || ''

				if (!summaryText) {
					print('Claude summary response missing summary field')
					return {
						fullText: responseText,
						summaryOnly: '',
					}
				}

				const normalizedSummary = summaryText
					.trim()
					.replace(/\n{3,}/g, '\n\n')
					.replace(/[•*-] /g, '• ')

				const cleanSummary = 'KEY POINTS:\n\n' + normalizedSummary

				return {
					fullText: `${responseText}\n\n---KEY POINTS---\n${normalizedSummary}`,
					summaryOnly: cleanSummary,
				}
			}

			print('Claude summary call failed with status ' + response.status)
			return {
				fullText: responseText,
				summaryOnly: '',
			}
		} catch (error) {
			print('Error in generateBulletSummary: ' + error)
			return {
				fullText: responseText,
				summaryOnly: '',
			}
		}
	}

	// Initialize location service
	initLocationService() {
		try {
			print('Initializing location service...')

			// Check if GeoLocation is available
			if (typeof GeoLocation === 'undefined') {
				print('Warning: GeoLocation module not available')
				return
			}

			this.locationService = GeoLocation.createLocationService()

			// Try maximum accuracy
			this.locationService.accuracy = GeoLocationAccuracy.Navigation // Most accurate

			// Start location updates immediately
			this.updateLocationEvent.reset(0.0)
			print('Location service initialized successfully')

			// Remove invalid permission check
		} catch (error) {
			print('Error initializing location service: ' + error)
		}
	}

	// Update location periodically
	updateLocation() {
		if (!this.locationService) {
			print('Location service not initialized')
			return
		}

		//created vision query
		this.locationService.getCurrentPosition(
			(geoPosition) => {
				this.latitude = geoPosition.latitude
				this.longitude = geoPosition.longitude

				// Enhanced location debugging
				print(
					`Location updated - Lat: ${this.latitude.toFixed(
						6
					)}, Long: ${this.longitude.toFixed(6)}`
				)
				print(`Location source: ${geoPosition.locationSource}`) // Will show if SIMULATED
				print(`Location timestamp: ${geoPosition.timestamp}`)
				print(`Location accuracy: ${geoPosition.horizontalAccuracy}m`)
			},
			(error) => {
				print('Error getting location: ' + error)
			}
		)

		// Schedule next update in 1 second
		this.updateLocationEvent.reset(20.0)
	}

	// Method to ping the local endpoint
	// async pingLocalEndpoint() {
	//   try {
	//     print("Pinging ngrok endpoint...");

	//     const request = new Request(`${this.backendBaseUrl}`,
	//       {
	//         method: "GET",
	//         headers: {
	//           "Content-Type": "application/json"
	//         }
	//       }
	//     );

	//     let response = await this.remoteServiceModule.fetch(request);
	//     print("Endpoint ping status: " + response.status);

	//     if (response.status === 200) {
	//       let responseData = await response.json();
	//       print("Endpoint response: " + JSON.stringify(responseData));
	//     } else {
	//       print("Endpoint ping failed with status: " + response.status);
	//     }
	//   } catch (error) {
	//     print("Error pinging endpoint: " + error);
	//   }
	// }

	async handleTriggerEnd(eventData) {
		if (this.isProcessing) {
			print('A request is already in progress. Please wait.')
			return
		}

		if (!this.textInput || !this.textInput.text) {
			print('Text input is missing or not assigned')
			return
		}

		// Save the user's query for adding to history later
		const userQuery = this.textInput.text

		try {
			this.isProcessing = true

			// Update UI
			if (this.LLM_analyse) {
				const processingMessage =
					'Hold on, conducting using your surroundings to fetch tailored responses...'
				this.LLM_analyse.text = this.makeTextWrappable(processingMessage)
			}

			let base64Image = ''

			// Encode image if available
			if (this.image) {
				const texture = this.image.mainPass.baseTex
				if (texture) {
					base64Image = (await this.encodeTextureToBase64(texture)) as string
					print('Image encoded to base64 successfully.')
				} else {
					print('Texture not found in the image component.')
				}
			}

			const backendUrl = this.getBackendUrl()
			if (!backendUrl) {
				print('Cannot call snap-and-buy because backend base URL is missing')
				return
			}

			if (!base64Image) {
				const warning =
					'No camera frame captured. Make sure an image component is wired before snapping.'
				print(warning)
				if (this.LLM_analyse) {
					this.LLM_analyse.text = this.makeTextWrappable(warning)
				}
				this.isProcessing = false
				return
			}

			const fetchModule = this.ensureFetchModule()

			const snapAndBuyPayload = {
				user_prompt: userQuery,
				latitude: this.latitude || 0,
				longitude: this.longitude || 0,
				image_surroundings: base64Image,
				chat_history: this.getChatHistoryString(),
				auto_purchase: this.snapPurchaseOptions.autoPurchase,
				database: this.snapPurchaseOptions.useCatalog,
				quantity: this.snapPurchaseOptions.quantity,
			}

			const fullUrl = `${backendUrl}/api/snap-purchase/snap-and-buy`
			print('Snap & Buy options locked to auto purchase + catalog + quantity 1')

			const request = new Request(fullUrl, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify(snapAndBuyPayload),
			})
			print('Posting to URL: ' + fullUrl)
			const response = await fetchModule.fetch(request)

			if (response.status === 200) {
				let responseData: SnapPurchaseResult | null = null
				let responseDisplay = ''

				try {
					responseData = (await response.json()) as SnapPurchaseResult
					print('Parsed snap-and-buy response successfully')

					responseDisplay = this.formatSnapAndBuyResponse(responseData)

					if (this.enableSummary && responseDisplay) {
						const result = await this.generateBulletSummary(responseDisplay)

						if (result.summaryOnly) {
							const displayText = result.summaryOnly
							if (this.textOutput) {
								this.textOutput.text = this.makeTextWrappable(displayText)
							}
							print(
								'Setting textOutput with summary, length: ' + displayText.length
							)
							this.addToHistory(userQuery, displayText)
						} else {
							if (this.textOutput) {
								this.textOutput.text = this.makeTextWrappable(responseDisplay)
							}
							this.addToHistory(userQuery, responseDisplay)
						}
					} else {
						if (this.textOutput) {
							this.textOutput.text = responseDisplay
						}
						this.addToHistory(userQuery, responseDisplay)
					}

					print('Snap-and-buy response: ' + responseDisplay)
				} catch (jsonError) {
					print('Error parsing snap-and-buy JSON: ' + jsonError)
					const errorText = 'Error parsing response: ' + jsonError
					if (this.textOutput) {
						this.textOutput.text = this.makeTextWrappable(errorText)
					}
				}

				if (this.LLM_analyse) {
					this.LLM_analyse.text = ''
				}

				if (this.ttsComponent && responseDisplay) {
					this.ttsComponent.generateAndPlaySpeech(responseDisplay)
				}
			} else {
				print(
					'Failure: Snap-and-buy API call failed with status ' + response.status
				)
				if (this.LLM_analyse) {
					const errorText = `❌ Error (HTTP ${response.status})\n\nBackend request failed.`
					this.LLM_analyse.text = this.makeTextWrappable(errorText)
				}
			}
		} catch (error) {
			print('Error in handleTriggerEnd: ' + error)
			if (this.LLM_analyse) {
				const errorText = `❌ Error\n\n${error}`
				this.LLM_analyse.text = this.makeTextWrappable(errorText)
			}
		} finally {
			this.isProcessing = false
		}
	}

	// More about encodeTextureToBase64: https://platform.openai.com/docs/guides/vision or https://developers.snap.com/api/lens-studio/Classes/OtherClasses#Base64
	encodeTextureToBase64(texture) {
		return new Promise((resolve, reject) => {
			Base64.encodeTextureAsync(
				texture,
				resolve,
				reject,
				CompressionQuality.LowQuality,
				EncodingType.Jpg
			)
		})
	}
}
