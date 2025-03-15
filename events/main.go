package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"github.com/charmbracelet/huh"
)

type Event struct {
	Type string
	Value []string 
}

type Config struct {
	Endpoints map[string]string
	Enabled   map[string]bool
}

var config = Config{
	Endpoints: map[string]string{
		"key_press": "http://localhost:5000/key_press",
		"focus": "http://localhost:6000/log",
		"full" : "http://localhost:8083/full",
	},
	Enabled: map[string]bool{
		"key_press":    true,
		"focus": true,
		"full": true,
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
			fmt.Println(event,endpoint)
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
			selected = append(selected, key)
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
						huh.NewOption("Full_Screen", "full"),
					).
					Value(&selected),
			),
		)

		if err := form.Run(); err != nil {
			fmt.Println("Error running form:", err)
			return
		}

		formRunOnce = true

		for key := range config.Enabled {
			config.Enabled[key] = false
		}
		for _, v := range selected {
			config.Enabled[v] = true
		}
	}

	fmt.Scanln()
}

