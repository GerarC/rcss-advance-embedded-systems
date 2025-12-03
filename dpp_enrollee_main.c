#include <string.h>
#include <math.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"

#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_netif.h"

#include "lwip/sockets.h"

#define WIFI_SSID       "TP-Link_6FEE"
#define WIFI_PASS       "98497089"
#define SERVER_IP       "192.168.0.125"
#define SERVER_PORT     5000

static const char *TAG = "WIFI_TCP";

QueueHandle_t command_queue;

// ------ ESTADO DEL BALÓN ------
float ball_dist = -1;
float ball_dir = 0;
float objetivo_dist = -1;
float objetivo_dir = 0;


// ------ ESTADO DEL PARTIDO ------
char game_state[32] = "unknown";

// ------ SOCKET GLOBAL ------
int socket_fd = -1;   // se actualiza dinámicamente en tcp_client_task


// ---------------------- EVENT HANDLER ----------------------
static void event_handler(void* arg, esp_event_base_t event_base,
                          int32_t event_id, void* event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
        ESP_LOGI(TAG, "WiFi STA START");
    }
    else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        ESP_LOGE(TAG, "WiFi desconectado. Reintentando...");
        esp_wifi_connect();
    }
    else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "Got IP: " IPSTR, IP2STR(&event->ip_info.ip));
    }
}


// ---------------------- WIFI INIT --------------------------
void wifi_init_sta(void)
{
    esp_netif_init();
    esp_event_loop_create_default();
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    wifi_config_t wifi_config = {
        .sta = {
            .ssid = WIFI_SSID,
            .password = WIFI_PASS,
            .threshold.authmode = WIFI_AUTH_WPA2_PSK,
        },
    };

    esp_wifi_init(&cfg);
    esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, event_handler, NULL);
    esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, event_handler, NULL);

    esp_wifi_set_mode(WIFI_MODE_STA);
    esp_wifi_set_config(WIFI_IF_STA, &wifi_config);
    esp_wifi_start();
}


// ---------------------- TCP CLIENT TASK --------------------
void tcp_client_task(void *pvParameters)
{
    vTaskDelay(pdMS_TO_TICKS(3000));  // Esperar WiFi

    struct sockaddr_in dest_addr = {0};
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(SERVER_PORT);
    dest_addr.sin_addr.s_addr = inet_addr(SERVER_IP);

    int init_enviado = 0;

    while (1) {

        // Crear socket
        socket_fd = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
        if (socket_fd < 0) {
            ESP_LOGE(TAG, "Error creando socket");
            vTaskDelay(pdMS_TO_TICKS(1000));
            continue;
        }

        ESP_LOGI(TAG, "Conectando al servidor intérprete...");

        if (connect(socket_fd, (struct sockaddr *)&dest_addr, sizeof(dest_addr)) != 0) {
            ESP_LOGE(TAG, "Error conectando: %d", errno);
            close(socket_fd);
            socket_fd = -1;
            vTaskDelay(pdMS_TO_TICKS(1500));
            continue;
        }

        ESP_LOGI(TAG, "¡Conectado!");

        if (!init_enviado) {
            const char *init_cmd = "init\n";
            send(socket_fd, init_cmd, strlen(init_cmd), 0);
            ESP_LOGI(TAG, "INIT enviado");
            init_enviado = 1;
        }

        char rx_buffer[256];

        while (1) {
            int len = recv(socket_fd, rx_buffer, sizeof(rx_buffer)-1, 0);

            if (len > 0) {
                rx_buffer[len] = '\0';
                ESP_LOGI(TAG, "RX: %s", rx_buffer);

                if (strncmp(rx_buffer, "referee ", 8) == 0) {
                    sscanf(rx_buffer, "referee %31s", game_state);
                    ESP_LOGI(TAG, "ESTADO: %s", game_state);
                }

                // Buscar "ball"
                char *p_ball = strstr(rx_buffer, "ball ");
                if (p_ball) {
                    sscanf(p_ball, "ball %f %f", &ball_dist, &ball_dir);
                }

                // Buscar "objetivo"
                char *p_obj = strstr(rx_buffer, "objetivo ");
                if (p_obj) {
                    sscanf(p_obj, "objetivo %f %f", &objetivo_dist, &objetivo_dir);
                }
            }
            else {
                ESP_LOGE(TAG, "Servidor cerró conexión");
                break;
            }
        }

        close(socket_fd);
        socket_fd = -1;

        vTaskDelay(pdMS_TO_TICKS(2000));
    }
}


// ---------------------- AI TASK ----------------------------
void ai_behavior_task(void *pvParameters)
{
    char cmd[64];
    TickType_t last_wake = xTaskGetTickCount();

    while (1) {
        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(100));

        if (strcmp(game_state, "kick_off_l") == 0) {
            strcpy(cmd, "kick 50 0");
            xQueueSend(command_queue, cmd, 0);
            continue;
        }

        if (strcmp(game_state, "play_on") == 0) {

            if (ball_dist < 0) continue;  // aún no veo el balón

            // 1. Alinearse hacia el balón
            if (ball_dist > 3) {

                if (ball_dir > 10)
                    sprintf(cmd, "turn %.1f", ball_dir);
                else if (ball_dir < -10)
                    sprintf(cmd, "turn %.1f", ball_dir);
                else
                    sprintf(cmd, "dash %d %.1f", 80, ball_dir);

                xQueueSend(command_queue, cmd, 0);
                continue;
            }
            else if(ball_dist > 0.7 && ball_dist < 3){
                sprintf(cmd, "dash %d %.1f", 20, ball_dir);

                xQueueSend(command_queue, cmd, 0);
                continue;
            }
            else if(ball_dist > 0.5 && ball_dist < 0.7){
                sprintf(cmd, "dash %d %.1f", 5, ball_dir);

                xQueueSend(command_queue, cmd, 0);
                continue;
            }

            // ----- Ahora estamos cerca del balón -----

            // 2. Dribbling: movernos hacia el objetivo mientras controlamos balón
            if (ball_dist <= 0.5 && objetivo_dist > 5) {

                // alinearse al objetivo
                sprintf(cmd, "kick 20 %.1f", objetivo_dir);

                xQueueSend(command_queue, cmd, 0);
                continue;
            }

            // 3. Ya estoy cerca del objetivo → tirar!!
            if (objetivo_dist <= 5) {
                strcpy(cmd, "kick 80 -30");
                xQueueSend(command_queue, cmd, 0);
                continue;
            }
        }


        // Antes del inicio del juego
        strcpy(cmd, "move -12 -20");
        xQueueSend(command_queue, cmd, 0);
    }
}


// ---------------------- CMD SENDER TASK --------------------
void cmd_sender_task(void *pvParameters)
{
    char cmd[64];

    while (1) {

        if (socket_fd >= 0 &&
            xQueueReceive(command_queue, cmd, portMAX_DELAY) == pdTRUE)
        {
            strcat(cmd, "\n");
            send(socket_fd, cmd, strlen(cmd), 0);
            ESP_LOGI(TAG, "TX: %s", cmd);
        }
    }
}


// ---------------------- APP MAIN ---------------------------
void app_main(void)
{
    nvs_flash_init();
    wifi_init_sta();

    command_queue = xQueueCreate(20, sizeof(char)*64);

    xTaskCreate(tcp_client_task, "tcp_client", 4096, NULL, 6, NULL);
    xTaskCreate(cmd_sender_task, "cmd_sender", 4096, NULL, 5, NULL);
    xTaskCreate(ai_behavior_task, "ai_behavior", 4096, NULL, 5, NULL);
}
