#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>

class ActionList;
class WifiNetworkList;

constexpr uint32_t SETTINGS_DEFAULT_SLEEP_TIMEOUT_MIN = 10;
constexpr const char* SETTINGS_DEFAULT_HOSTNAME = "tiny-engineer";
#if defined(TE_BOARD_SUPERMINI)
constexpr uint8_t SETTINGS_DEFAULT_VOLUME = 100;
#else
constexpr uint8_t SETTINGS_DEFAULT_VOLUME = 70;
#endif
constexpr bool SETTINGS_DEFAULT_WELCOME = true;
constexpr bool SETTINGS_DEFAULT_SERIAL_LOG = false;
constexpr bool SETTINGS_DEFAULT_PUSH_BUTTON = false;
constexpr uint8_t SETTINGS_DEFAULT_PUSH_BUTTON_PIN = 20;
constexpr const char* SETTINGS_DEFAULT_PUSH_BUTTON_SOUND = "none";
constexpr size_t SETTINGS_PUSH_BUTTON_SOUND_MAX_LEN = 8;
constexpr uint32_t SETTINGS_DEFAULT_CONTINUOUS_TIMEOUT_MIN = 5;
constexpr const char* SETTINGS_DEFAULT_LOADING = "progress";
constexpr const char* SETTINGS_DEFAULT_EYES_STYLE = "classic";
constexpr const char* SETTINGS_DEFAULT_ACCESS_TOKEN = "";
// Empty = unprovisioned. "wifi" or "usb" after the setup wizard finishes.
constexpr const char* SETTINGS_DEFAULT_LINK_MODE = "";
constexpr size_t SETTINGS_LINK_MODE_MAX_LEN = 8;

constexpr uint32_t SETTINGS_SLEEP_TIMEOUT_MIN_MIN = 1;
constexpr uint32_t SETTINGS_SLEEP_TIMEOUT_MAX_MIN = 1440;
constexpr size_t SETTINGS_HOSTNAME_MAX_LEN = 31;
constexpr size_t SETTINGS_LOADING_MAX_LEN = 15;
constexpr size_t SETTINGS_EYES_STYLE_MAX_LEN = 15;
constexpr size_t SETTINGS_ACCESS_TOKEN_MAX_LEN = 64;
constexpr size_t SETTINGS_WIFI_SSID_MAX_LEN = 32;
constexpr size_t SETTINGS_WIFI_PASSWORD_MAX_LEN = 63;
constexpr size_t SETTINGS_WIFI_NETWORK_MAX = 5;
constexpr uint8_t SETTINGS_VOLUME_MAX = 100;
constexpr uint32_t SETTINGS_CONTINUOUS_TIMEOUT_MIN_MIN = 1;
constexpr uint32_t SETTINGS_CONTINUOUS_TIMEOUT_MAX_MIN = 1440;
constexpr size_t SETTINGS_SERVO_COUNT = 5;
constexpr uint8_t SETTINGS_SERVO_ANGLE_MAX = 180;
constexpr size_t SETTINGS_RGB_ORDER_MAX_LEN = 3;
#if defined(TE_BOARD_SUPERMINI)
// SuperMini build: discrete RGB LED wired R/G/B on GP6/7/10, OLED mounted upside down.
constexpr const char* SETTINGS_DEFAULT_RGB_ORDER = "RGB";
constexpr bool SETTINGS_DEFAULT_OLED_ROTATE_180 = true;
#else
constexpr const char* SETTINGS_DEFAULT_RGB_ORDER = "GRB";
constexpr bool SETTINGS_DEFAULT_OLED_ROTATE_180 = false;
#endif
// Wi-Fi transmit power cap in quarter-dBm (ESP-IDF units), sent as dBm on the
// API. 20 dBm is the ESP32-C3 PHY default, so the stock board keeps its power.
#if defined(TE_BOARD_SUPERMINI)
// The SuperMini's antenna is unreliable at full power; 8.5 dBm is the board-tested start.
constexpr uint8_t SETTINGS_DEFAULT_WIFI_TX_POWER_QDBM = 34;
#else
constexpr uint8_t SETTINGS_DEFAULT_WIFI_TX_POWER_QDBM = 80;
#endif
constexpr uint8_t SETTINGS_WIFI_TX_POWER_MIN_QDBM = 8;   // 2 dBm
constexpr uint8_t SETTINGS_WIFI_TX_POWER_MAX_QDBM = 80;  // 20 dBm

struct ServoRanges {
  uint8_t mins[SETTINGS_SERVO_COUNT];
  uint8_t maxs[SETTINGS_SERVO_COUNT];

  // Every angle within 0..SETTINGS_SERVO_ANGLE_MAX and each min below its max.
  bool valid() const;
};

// Fields left empty, or nullptr for text, keep their saved value.
struct SettingsPatch {
  std::optional<uint32_t> sleepTimeoutMin;
  const char* hostname = nullptr;
  std::optional<uint8_t> volume;
  std::optional<bool> welcome;
  std::optional<bool> serialLog;
  std::optional<bool> pushButton;
  std::optional<uint8_t> pushButtonPin;
  std::optional<uint32_t> continuousTimeoutMin;
  const char* loading = nullptr;
  const char* eyesStyle = nullptr;
  const char* accessToken = nullptr;
  const char* linkMode = nullptr;
  std::optional<ServoRanges> servoRanges;
  const char* rgbOrder = nullptr;
  std::optional<bool> oledRotate180;
  // dBm, 2-20 in 0.5 dBm steps.
  std::optional<float> wifiTxPowerDbm;

  // API name of the first field set to an invalid value, or nullptr.
  const char* invalidField() const;

  // Name of the setup wizard step that owns a field the patch sets (servo
  // ranges, RGB order, screen rotation), or nullptr. Those save only in setup AP mode.
  const char* setupOnlyStep() const;
};

void initSettings();

uint32_t settingsSleepTimeoutMin();
uint32_t settingsSleepTimeoutMs();
const char* settingsHostname();
uint8_t settingsVolume();
bool settingsWelcomeEnabled();
bool settingsSerialLogEnabled();
bool settingsPushButton();
uint8_t settingsPushButtonPin();
uint32_t settingsContinuousTimeoutMin();
const char* settingsLoading();
const char* settingsEyesStyle();
const char* settingsAccessToken();
bool settingsAccessTokenSet();
const WifiNetworkList& settingsWifiNetworks();
bool settingsWifiConfigured();
const ActionList& settingsActions();
const char* settingsLinkMode();
// True after setup chose Wi-Fi or USB-only (migrated devices with saved nets count).
bool settingsProvisioned();
bool settingsValidateLinkMode(const char* linkMode);
// Pure gate for tests: nullptr if the patch may change link_mode, else a short error.
// Setup AP may set mode; outside AP only a no-op (same value) is allowed.
const char* settingsLinkModePatchDenied(
  const char* patchMode,
  const char* currentMode,
  bool provisioned,
  bool inSetupAp
);
float settingsServoMin(int index);
float settingsServoMax(int index);
const char* settingsRgbOrder();
bool settingsOledRotate180();
// Saved Wi-Fi TX power cap in quarter-dBm.
uint8_t settingsWifiTxPowerQdbm();

// True once the saved hostname, loading screen or WiFi networks differ from
// what this boot started with; those apply only after a reboot.
bool settingsRebootRequired();

bool settingsValidateSleepTimeout(uint32_t sleepTimeoutMin);
bool settingsValidateHostname(const char* hostname);
bool settingsValidateVolume(uint8_t volume);
bool settingsValidateContinuousTimeout(uint32_t continuousTimeoutMin);
bool settingsValidateLoading(const char* loading);
bool settingsValidateEyesStyle(const char* eyesStyle);
bool settingsValidateAccessToken(const char* accessToken);
bool settingsValidateWifiSsid(const char* wifiSsid);
bool settingsValidateWifiPassword(const char* wifiPassword);
bool settingsValidateRgbOrder(const char* rgbOrder);
bool settingsValidatePushButtonPin(uint8_t pin);
bool settingsValidatePushButtonSound(const char* sound);
// 2-20 dBm in 0.5 dBm steps.
bool settingsValidateWifiTxPowerDbm(float dbm);
// Quarter-dBm form of the same rule, for values read back from NVS.
bool settingsValidateWifiTxPowerQdbm(uint32_t qdbm);
uint8_t settingsWifiTxPowerDbmToQdbm(float dbm);

// True when applying the patch would leave two enabled extensions on the same GPIO.
// Writes a plain conflict message when message/messageLen are set. Does not write NVS.
bool settingsWouldPinConflict(
  const SettingsPatch& patch,
  char* message = nullptr,
  size_t messageLen = 0
);

// Saves the fields the patch sets and keeps the others. False when a field is
// invalid (nothing is written), pin claims conflict, or NVS fails.
bool saveSettings(const SettingsPatch& patch);

// Replaces every saved network in RAM and NVS.
bool saveWifiNetworks(const WifiNetworkList& networks);

// Replaces every saved Action in RAM and NVS. False when NVS fails.
bool saveActions(const ActionList& actions);

// Clears the NVS namespace and restores the defaults, WiFi networks included,
// but keeps the servo min/max, RGB LED byte order and OLED 180° rotation.
bool factoryResetSettings();
