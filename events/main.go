package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/charmbracelet/huh"
)

type Event struct {
	Type  string
	Value []string
}

type Config struct {
	Endpoints map[string]string
	Enabled   map[string]bool
}

var config = Config{
	Endpoints: map[string]string{
		"key_press": "http://localhost:5000/key_press",
		"focus":     "http://localhost:6000/log",
		"sus_aud":   "http://localhost:6000/log",
		"sus_vid":   "http://localhost:6000/log",
		"media":     "http://localhost:7000/media",
	},
	Enabled: map[string]bool{
		"key_press": true,
		"focus":     true,
		"sus_aud":   true,
		"sus_vid":   true,
		"media":     true,
	},
}

func publishHandler(w http.ResponseWriter, r *http.Request) {
	var requestData struct {
		Data []Event `json:"data"`
	}

	// Decode JSON request
	if err := json.NewDecoder(r.Body).Decode(&requestData); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	fmt.Println(requestData)
	// Process each event
	for _, event := range requestData.Data {
		endpoint, exists := config.Endpoints[event.Type]
		if exists && config.Enabled[event.Type] {
			fmt.Println(event, endpoint)
			forwardEvent(endpoint, event)
		}
	}

	fmt.Fprintf(w, "Events received successfully")
}

func forwardEvent(endpoint string, event Event) {
	jsonData, _ := json.Marshal(event)
	resp, err := http.Post(endpoint, "application/json", bytes.NewReader(jsonData))
	if err != nil {
		fmt.Println("Error forwarding event:", err)
		return
	}
	resp.Body.Close()
}

var formRunOnce bool = false

func main() {
	// HTTP server
	go func() {
		http.HandleFunc("/publish", publishHandler)
		fmt.Println("Server started on :8080")
		http.ListenAndServe(":8080", nil)
	}()

	selected := []string{}
	for key, enabled := range config.Enabled {
		if enabled {
			// Map internal event types to UI options
			if key == "sus_aud" || key == "sus_vid" {
				if !contains(selected, "media") {
					selected = append(selected, "media")
				}
			} else {
				selected = append(selected, key)
			}
		}
	}

	if !formRunOnce {
		form := huh.NewForm(
			huh.NewGroup(
				huh.NewMultiSelect[string]().
					Title("Enable/Disable Endpoints").
					Options(
						huh.NewOption("Key_Press", "key_press"),
						huh.NewOption("Window_Focus", "focus"),
						huh.NewOption("Audio/Video", "media"),
					).
					Value(&selected),
			),
		)

		if err := form.Run(); err != nil {
			fmt.Println("Error running form:", err)
			return
		}

		formRunOnce = true

		// Reset all options first
		for key := range config.Enabled {
			config.Enabled[key] = false
		}

		// Apply the selected options with proper mapping
		for _, v := range selected {
			config.Enabled[v] = true

			// If "media" is selected, enable both audio and video events
			if v == "media" {
				config.Enabled["sus_aud"] = true
				config.Enabled["sus_vid"] = true
			}
		}
	}

	fmt.Println("Current configuration:")
	for key, enabled := range config.Enabled {
		fmt.Printf("- %s: %v\n", key, enabled)
	}

	fmt.Scanln()
}

// Helper function to check if a slice contains a string
func contains(slice []string, s string) bool {
	for _, item := range slice {
		if item == s {
			return true
		}
	}
	return false
}
