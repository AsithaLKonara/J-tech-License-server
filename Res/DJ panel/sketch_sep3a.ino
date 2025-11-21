#include <LittleFS.h>
#include <FastLED.h>

#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB
#define DATA_PIN    3

// Configuration settings - modify these as needed
int brightness = 255;           // LED brightness (0-255)
int frameDelay = 120;           // Delay between frames in milliseconds
int numLeds = 50;             // Number of LEDs in strip
bool isGRBMode = true;        // Color order: true=GRB, false=RGB

const int maxBrightness = 240;  // Maximum brightness cap

CRGB *leds;
File ledFile;

// Dynamic arrays for unlimited .bin files
String *animationFiles = nullptr;
int numAnimations = 0;
int currentAnimationIndex = 0;  // Current animation being played

unsigned long lastFrameTime = 0;  // To track time for frame updates

void setup() {
  Serial.begin(115200);
  Serial.println("Starting LED Animation Player with LittleFS...");

  // Initialize LittleFS
  if (!LittleFS.begin()) {
    Serial.println("LittleFS initialization failed!");
    return;
  }
  Serial.println("LittleFS initialized.");

  // Apply brightness cap
  brightness = constrain(brightness, 0, maxBrightness);
  
  // Initialize LED strip
  leds = new CRGB[numLeds];
  FastLED.addLeds<LED_TYPE, DATA_PIN, COLOR_ORDER>(leds, numLeds).setCorrection(TypicalLEDStrip);
  FastLED.setBrightness(brightness);
  
  // Print current settings
  printSettings();
  
  // Scan for .bin files in LittleFS
  scanBinFiles();
  
  if (numAnimations > 0) {
    Serial.println("Starting with first animation...");
    openAnimationFile(0);  // Start with first animation
  } else {
    Serial.println("No .bin animation files found!");
  }
}

void loop() {
  // Only proceed if we have animations
  if (numAnimations == 0) {
    return;
  }

  // Read animation frames from file only if enough time has passed
  if (millis() - lastFrameTime >= frameDelay) {
    lastFrameTime = millis();  // Update last frame time

    if (ledFile.available()) {
      for (int i = 0; i < numLeds; i++) {
        if (ledFile.available() < 3) {
          ledFile.seek(0);  // Loop the current file if not enough data
          break;
        }

        byte r, g, b;
        if (isGRBMode) {
          g = ledFile.read();
          r = ledFile.read();
          b = ledFile.read();
        } else {
          r = ledFile.read();
          g = ledFile.read();
          b = ledFile.read();
        }

        leds[i] = CRGB(r, g, b);
      }

      FastLED.show();
    } else {
      nextAnimation();  // Switch to the next animation when current one finishes
    }
  }
}

void printSettings() {
  Serial.println("=== Current Settings ===");
  Serial.println("Brightness: " + String(brightness));
  Serial.println("Frame Delay: " + String(frameDelay) + " ms");
  Serial.println("Number of LEDs: " + String(numLeds));
  Serial.println("Color Order: " + String(isGRBMode ? "GRB" : "RGB"));
  Serial.println("Max Brightness Cap: " + String(maxBrightness));
  Serial.println("========================");
}

// Scan LittleFS root directory for .bin files
void scanBinFiles() {
  Dir dir = LittleFS.openDir("/");
  
  // First pass: count .bin files
  int fileCount = 0;
  while (dir.next()) {
    if (!dir.isDirectory()) {
      String fileName = dir.fileName();
      
      // Check if file ends with .bin (lowercase only)
      if (fileName.endsWith(".bin")) {
        fileCount++;
      }
    }
  }
  
  if (fileCount == 0) {
    Serial.println("No .bin files found in LittleFS");
    return;
  }

  // Allocate memory for animation files array
  animationFiles = new String[fileCount];
  numAnimations = 0;

  // Reset directory reading
  dir = LittleFS.openDir("/");
  
  // Second pass: store .bin file names
  while (dir.next() && numAnimations < fileCount) {
    if (!dir.isDirectory()) {
      String fileName = dir.fileName();
      
      // Check if file ends with .bin (lowercase only)
      if (fileName.endsWith(".bin")) {
        animationFiles[numAnimations] = fileName;
        Serial.println("Found .bin file: " + fileName);
        numAnimations++;
      }
    }
  }
  
  // Sort animation files alphabetically
  sortAnimationFiles();
  
  Serial.println("Total .bin files loaded: " + String(numAnimations));
  Serial.println("Files will be played in this order:");
  for (int i = 0; i < numAnimations; i++) {
    Serial.println(String(i + 1) + ". " + animationFiles[i]);
  }
}

// Sort animation files in alphabetical order
void sortAnimationFiles() {
  if (numAnimations <= 1) {
    return; // No need to sort if 0 or 1 files
  }
  
  // Simple bubble sort for file names
  for (int i = 0; i < numAnimations - 1; i++) {
    for (int j = 0; j < numAnimations - i - 1; j++) {
      if (animationFiles[j].compareTo(animationFiles[j + 1]) > 0) {
        // Swap the strings
        String temp = animationFiles[j];
        animationFiles[j] = animationFiles[j + 1];
        animationFiles[j + 1] = temp;
      }
    }
  }
}

void openAnimationFile(int index) {
  if (ledFile) {
    ledFile.close();
  }

  if (index < 0 || index >= numAnimations) {
    Serial.println("Invalid animation index: " + String(index));
    return;
  }

  String fileName = animationFiles[index];
  ledFile = LittleFS.open(fileName, "r");
  if (!ledFile) {
    Serial.println("Error opening animation file: " + fileName);
    // Try next file if current fails
    nextAnimation();
    return;
  }

  ledFile.seek(0);  // Always start from beginning
  Serial.println("Animation file opened: " + fileName + " (Index: " + String(index) + ")");
}

void nextAnimation() {
  if (numAnimations == 0) {
    return;
  }
  
  // Move to next animation, loop back to 0 after last file
  currentAnimationIndex = (currentAnimationIndex + 1) % numAnimations;
  Serial.println("Switching to next animation: " + String(currentAnimationIndex + 1) + "/" + String(numAnimations));
  openAnimationFile(currentAnimationIndex);
}