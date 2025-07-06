// Setup I2C for DHT20 sensor
I2C1.setup({sda: B7, scl: B6});

// Setup SPI for SD card
SPI1.setup({mosi: B5, miso: B4, sck: B3});
E.connectSDCard(SPI1, B10);

// Constants
const VOLTAGE_THRESHOLD = 3.0;
const R1 = 10000; // 10kΩ
const R2 = 3300;  // 3.3kΩ
const ADC_PIN = B1;

// Pad single-digit numbers with leading zero
function pad(n) {
  return (n < 10 ? "0" : "") + n;
}

// Function to initialize CSV file with headers
function initializeLogFile() {
  try {
    let logFile = E.openFile("data.csv", "w");
    logFile.write("Timestamp,Temperature,Humidity\n");
    logFile.close();
    console.log("CSV file initialized with headers");
  } catch(e) {
    console.log("Error creating CSV file:", e);
  }
}

// Function to read voltage from the voltage divider
function readVoltage() {
  const adcValue = analogRead(ADC_PIN);
  const voltage = adcValue * (R1 + R2) / R2 * 3.3;
  console.log("Voltage: " + voltage.toFixed(3) + " V");
  return voltage;
}

// Function to read data from DHT20 sensor
function readDHT20() {
  I2C1.writeTo(0x38, [0xAC, 0x33, 0x00]);
  setTimeout(function() {
    const data = I2C1.readFrom(0x38, 7);
    const humidity = ((data[1] << 12) | (data[2] << 4) | (data[3] >> 4)) * 9.5367431640625e-5;
    const temperature = (((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]) * 1.9073486328125e-4 - 50;
    console.log("Temperature: " + temperature.toFixed(2) + " °C, Humidity: " + humidity.toFixed(2) + " %");
    
    logData(temperature, humidity);
  }, 100);
}

// Function to log data in CSV format
function logData(temperature, humidity) {
  const now = new Date();
  const dateStr = now.getFullYear() + "-" +
                  pad(now.getMonth()+1) + "-" +
                  pad(now.getDate());
  const timeStr = pad(now.getHours()) + ":" +
                  pad(now.getMinutes()) + ":" +
                  pad(now.getSeconds());
  const timestamp = dateStr + " " + timeStr;

  try {
    let logFile = E.openFile("data.csv", "a");
    logFile.write(
      timestamp + "," +
      temperature.toFixed(2) + "," +
      humidity.toFixed(2) + "\n"
    );
    logFile.close();
    console.log("[" + timestamp + "] Data logged to CSV");
  } catch(e) {
    console.log("Error logging to CSV:", e);
  }
}

// Main function to check voltage and read sensor
function checkVoltageAndReadSensor() {
  const voltage = readVoltage();
  if (voltage >= VOLTAGE_THRESHOLD) {
    readDHT20();
  } else {
    console.log("Voltage below threshold, going to sleep");
    setDeepSleep(1);
  }
}

// Initialize CSV file on startup
initializeLogFile();

// Set interval to check every 10 seconds
setInterval(checkVoltageAndReadSensor, 10000);

// Enable deep sleep & indicators
setDeepSleep(1);
setSleepIndicator(LED1);
setBusyIndicator(LED2);

// Initial voltage check
setTimeout(checkVoltageAndReadSensor, 1000);