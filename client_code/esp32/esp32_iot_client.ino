/*
 * ESP32 IoT客户端 - Arduino IDE版本
 * 连接到Flask服务器并发送传感器数据
 * 支持多种传感器和GPIO控制
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Wire.h>
#include <BMP280.h>

// WiFi配置
const char* ssid = "YourWiFiName";
const char* password = "YourWiFiPassword";

// 服务器配置
const char* serverURL = "http://192.168.1.100:5000";
const String deviceID = "esp32_001";
const String deviceName = "ESP32 Sensor Hub";

// 传感器引脚配置
#define DHT_PIN 4
#define DHT_TYPE DHT22
#define MOTION_PIN 5
#define LIGHT_PIN A0
#define TRIG_PIN 18
#define ECHO_PIN 19
#define LED_PIN 2
#define RELAY_PIN 23

// 传感器对象
DHT dht(DHT_PIN, DHT_TYPE);
BMP280 bmp;

// 全局变量
unsigned long lastHeartbeat = 0;
unsigned long lastDataSend = 0;
const unsigned long heartbeatInterval = 30000;  // 30秒
const unsigned long dataSendInterval = 10000;   // 10秒
bool serverConnected = false;

void setup() {
  Serial.begin(115200);
  
  // 初始化引脚
  pinMode(LED_PIN, OUTPUT);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(MOTION_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  // 初始化传感器
  dht.begin();
  Wire.begin();
  
  if (!bmp.begin()) {
    Serial.println("BMP280 sensor not found!");
  }
  
  // 连接WiFi
  connectWiFi();
  
  // 注册设备
  registerDevice();
  
  Serial.println("ESP32 IoT Client started");
  digitalWrite(LED_PIN, HIGH);  // 启动指示灯
}

void loop() {
  unsigned long currentTime = millis();
  
  // 检查WiFi连接
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, reconnecting...");
    connectWiFi();
  }
  
  // 发送心跳
  if (currentTime - lastHeartbeat >= heartbeatInterval) {
    sendHeartbeat();
    lastHeartbeat = currentTime;
  }
  
  // 发送传感器数据
  if (currentTime - lastDataSend >= dataSendInterval) {
    sendSensorData();
    lastDataSend = currentTime;
  }
  
  // 检查服务器命令
  checkServerCommands();
  
  delay(1000);
}

void connectWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.print("WiFi connected! IP: ");
    Serial.println(WiFi.localIP());
    digitalWrite(LED_PIN, HIGH);
  } else {
    Serial.println();
    Serial.println("WiFi connection failed!");
    digitalWrite(LED_PIN, LOW);
  }
}

void registerDevice() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  HTTPClient http;
  http.begin(String(serverURL) + "/api/esp32/register");
  http.addHeader("Content-Type", "application/json");
  
  // 构建注册数据
  DynamicJsonDocument doc(1024);
  doc["device_id"] = deviceID;
  doc["name"] = deviceName;
  doc["description"] = "ESP32 with multiple sensors";
  doc["wifi_ssid"] = ssid;
  doc["ip_address"] = WiFi.localIP().toString();
  doc["mac_address"] = WiFi.macAddress();
  doc["firmware_version"] = "1.0.0";
  doc["chip_model"] = "ESP32";
  
  JsonArray sensors = doc.createNestedArray("sensors");
  sensors.add("temperature");
  sensors.add("humidity");
  sensors.add("pressure");
  sensors.add("light");
  sensors.add("motion");
  sensors.add("distance");
  
  JsonArray capabilities = doc.createNestedArray("capabilities");
  capabilities.add("wifi");
  capabilities.add("gpio");
  capabilities.add("pwm");
  capabilities.add("adc");
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Registration response: " + response);
    
    DynamicJsonDocument responseDoc(512);
    deserializeJson(responseDoc, response);
    
    if (responseDoc["success"]) {
      serverConnected = true;
      Serial.println("Device registered successfully");
    }
  } else {
    Serial.println("Registration failed: " + String(httpResponseCode));
  }
  
  http.end();
}

void sendHeartbeat() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  HTTPClient http;
  http.begin(String(serverURL) + "/api/esp32/heartbeat");
  http.addHeader("Content-Type", "application/json");
  
  DynamicJsonDocument doc(512);
  doc["device_id"] = deviceID;
  
  JsonObject systemInfo = doc.createNestedObject("system_info");
  systemInfo["free_heap"] = ESP.getFreeHeap();
  systemInfo["wifi_rssi"] = WiFi.RSSI();
  systemInfo["uptime"] = millis();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    Serial.println("Heartbeat sent successfully");
  } else {
    Serial.println("Heartbeat failed: " + String(httpResponseCode));
    serverConnected = false;
  }
  
  http.end();
}

void sendSensorData() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  HTTPClient http;
  http.begin(String(serverURL) + "/api/esp32/data");
  http.addHeader("Content-Type", "application/json");
  
  DynamicJsonDocument doc(1024);
  doc["device_id"] = deviceID;
  
  // 读取DHT22传感器
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  if (!isnan(temperature) && !isnan(humidity)) {
    doc["temperature"] = temperature;
    doc["humidity"] = humidity;
  }
  
  // 读取BMP280传感器
  if (bmp.begin()) {
    doc["pressure"] = bmp.readPressure() / 100.0;  // 转换为hPa
  }
  
  // 读取光照传感器
  int lightValue = analogRead(LIGHT_PIN);
  doc["light"] = map(lightValue, 0, 4095, 0, 1000);  // 映射到0-1000 lux
  
  // 读取运动传感器
  doc["motion"] = digitalRead(MOTION_PIN);
  
  // 读取超声波距离传感器
  float distance = readUltrasonicDistance();
  if (distance > 0) {
    doc["distance"] = distance;
  }
  
  // 系统状态
  JsonObject systemStatus = doc.createNestedObject("system_status");
  systemStatus["free_heap"] = ESP.getFreeHeap();
  systemStatus["wifi_rssi"] = WiFi.RSSI();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Data sent successfully");
    
    // 闪烁LED表示数据发送成功
    digitalWrite(LED_PIN, LOW);
    delay(100);
    digitalWrite(LED_PIN, HIGH);
  } else {
    Serial.println("Data send failed: " + String(httpResponseCode));
  }
  
  http.end();
}

float readUltrasonicDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // 30ms超时
  
  if (duration == 0) {
    return -1;  // 超时或无回波
  }
  
  float distance = duration * 0.034 / 2;  // 计算距离（cm）
  
  if (distance > 400) {
    return -1;  // 超出测量范围
  }
  
  return distance;
}

void checkServerCommands() {
  // 这里可以实现轮询服务器命令的逻辑
  // 或者使用WebSocket进行实时通信
  
  if (WiFi.status() != WL_CONNECTED || !serverConnected) return;
  
  HTTPClient http;
  http.begin(String(serverURL) + "/api/esp32/config/" + deviceID);
  
  int httpResponseCode = http.GET();
  
  if (httpResponseCode == 200) {
    String response = http.getString();
    
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, response);
    
    if (doc["success"]) {
      JsonObject config = doc["config"];
      
      // 处理配置更新
      if (config.containsKey("led_brightness")) {
        int brightness = config["led_brightness"];
        analogWrite(LED_PIN, brightness);
      }
      
      if (config.containsKey("relay_state")) {
        bool relayState = config["relay_state"];
        digitalWrite(RELAY_PIN, relayState ? HIGH : LOW);
      }
      
      if (config.containsKey("data_interval")) {
        // 更新数据发送间隔
        // dataSendInterval = config["data_interval"];
      }
    }
  }
  
  http.end();
}

void executeControlCommand(String action, JsonObject parameters) {
  if (action == "gpio_write") {
    int pin = parameters["pin"];
    int value = parameters["value"];
    digitalWrite(pin, value);
    Serial.println("GPIO " + String(pin) + " set to " + String(value));
  }
  else if (action == "pwm_write") {
    int pin = parameters["pin"];
    int value = parameters["value"];
    analogWrite(pin, value);
    Serial.println("PWM " + String(pin) + " set to " + String(value));
  }
  else if (action == "led_control") {
    int brightness = parameters["brightness"];
    analogWrite(LED_PIN, brightness);
    Serial.println("LED brightness set to " + String(brightness));
  }
  else if (action == "relay_control") {
    bool state = parameters["state"];
    digitalWrite(RELAY_PIN, state ? HIGH : LOW);
    Serial.println("Relay " + String(state ? "ON" : "OFF"));
  }
  else if (action == "restart") {
    Serial.println("Restarting ESP32...");
    delay(1000);
    ESP.restart();
  }
  else if (action == "deep_sleep") {
    int duration = parameters["duration"];
    Serial.println("Entering deep sleep for " + String(duration) + " seconds");
    esp_sleep_enable_timer_wakeup(duration * 1000000);  // 微秒
    esp_deep_sleep_start();
  }
  else if (action == "wifi_reconnect") {
    Serial.println("Reconnecting WiFi...");
    WiFi.disconnect();
    delay(1000);
    connectWiFi();
  }
}

