package main

import (
    "io"
    "net/http"
)

func main() {
    http.HandleFunc("/stream", func(w http.ResponseWriter, r *http.Request) {
        resp, err := http.Get("http://192.168.1.84:8000")
        if err != nil {
            http.Error(w, "Camera not reachable", http.StatusBadGateway)
            return
        }
        defer resp.Body.Close()

        for k, v := range resp.Header {
            w.Header()[k] = v
        }

        w.WriteHeader(resp.StatusCode)
        io.Copy(w, resp.Body)
    })

    http.ListenAndServe(":8080", nil)
}