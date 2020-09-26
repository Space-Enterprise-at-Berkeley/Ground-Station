#include <math.h>

#define LOW_PRESSURE_1 A0
#define LOW_PRESSURE_2 A1
#define LOW_PRESSURE_3 A2
#define LOW_PRESSURE_4 A3

#define HIGH_PRESSURE_1 A4
#define HIGH_PRESSURE_2 A5

#define LOX_2 2
#define LOX_5 3
#define LOX_GEMS 4

#define PROP_2 8
#define PROP_5 9
#define PROP_GEMS 10

//#define RFSerial Serial1

// start solenoid states

int lox2_state = LOW;
int lox5_state = LOW;
int lox_gems_state = LOW;

int prop2_state = LOW;
int prop5_state = LOW;
int prop_gems_state = LOW;

// end solenoid states

void readData();
void convertData();

int input = 0;
bool shouldPrint = true;

long currTime = millis();
long currTime2 = millis();

int numLowPressure = 0;
int numHighPressure = 0;

void setup() {
  Serial.begin(9600);
  //Setup and start RF communication
//  RFSerial.begin(57600);

  //while(!Serial.available());
  
  pinMode(LOX_2, OUTPUT);
  pinMode(LOX_5, OUTPUT);
  pinMode(LOX_GEMS, OUTPUT);

  pinMode(PROP_2, OUTPUT);
  pinMode(PROP_5, OUTPUT);
  pinMode(PROP_GEMS, OUTPUT);

  digitalWrite(LOX_2, lox2_state);
  digitalWrite(LOX_5, lox5_state);
  digitalWrite(LOX_GEMS, lox_gems_state);

  digitalWrite(PROP_2, prop2_state);
  digitalWrite(PROP_5, prop5_state);
  digitalWrite(PROP_GEMS, prop_gems_state);
  
  
Serial.println("How many low pressure sensors are connected?");
  while (Serial.available() == 0) {
    
      delay(50);
      if (millis() - currTime > 2000) {
        Serial.println("waiting for low pt #...");
        currTime = millis();
      }
    }
  numLowPressure = Serial.parseInt();
  
//  numLowPressure = Serial.read() - 48;
  
Serial.println("How many high pressure sensors are connected?");
  while (Serial.available() == 0) {
      delay(50);
      if (millis() - currTime > 2000) {
        Serial.println("waiting for high pt #...");
        currTime = millis();
      }
    }

  numHighPressure = Serial.parseInt();

  Serial.print("There are ");
  Serial.print(numLowPressure);
  Serial.print(" low PTs and ");
  Serial.print(numHighPressure);
  Serial.println(" high PTs");

  if(numLowPressure >= 1){
    pinMode(LOW_PRESSURE_1, INPUT);
    Serial.print("low1,");
  }
  if(numLowPressure >= 2){
    pinMode(LOW_PRESSURE_2, INPUT);
    Serial.print("low2,");
  }
  if(numLowPressure >= 3){
    pinMode(LOW_PRESSURE_3, INPUT);
    Serial.print("low3,");
  }
  if(numLowPressure >= 4){
    pinMode(LOW_PRESSURE_4, INPUT);
    Serial.print("low4,");
  }

  if(numHighPressure >= 1){
    pinMode(HIGH_PRESSURE_1, INPUT);
    Serial.print("high1,");
  }
  if(numHighPressure >= 2){
    pinMode(HIGH_PRESSURE_2, INPUT);
    Serial.print("high2,");
  }
  Serial.print("\n");

  currTime = millis();
  currTime2 = millis();
}

// 0.88V - 4.4V : ?? - 5000 PSI

int lowPressure1, lowPressure2, lowPressure3, lowPressure4, highPressure1, highPressure2;
int convertedLow1, convertedLow2, convertedLow3, convertedLow4, convertedHigh1, convertedHigh2;

int periodic = 100; // take data 10 times a second.
void loop() {
  currTime = millis();
  if((currTime%int(periodic)) == 0) {
    if (Serial.available() > 0) {
       char readByte = Serial.read();
      if(readByte == 'a'){
        lox2_state = toggle(lox2_state);
        digitalWrite(LOX_2, lox2_state);
        Serial.print("Toggled LOX 2: ");
        Serial.println(lox2_state);
      } else if(readByte == 'b'){
        lox5_state = toggle(lox5_state);
        digitalWrite(LOX_5, lox5_state);
        Serial.print("Toggled LOX 5: ");
        Serial.println(lox5_state);
      } else if (readByte == 'c'){
        lox_gems_state = toggle(lox_gems_state);
        digitalWrite(LOX_GEMS, lox_gems_state);
        Serial.print("Toggled LOX Gems: ");
        Serial.println(lox_gems_state);
      } else if(readByte == 'x'){
        prop2_state = toggle(prop2_state);
        digitalWrite(PROP_2, prop2_state);
        Serial.print("Toggled PROP 2: ");
        Serial.println(prop2_state);
      } else if (readByte == 'y') {
        prop5_state = toggle(prop5_state);
        digitalWrite(PROP_5, prop5_state);
        Serial.print("Toggled PROP 5: ");
        Serial.println(prop5_state);
      } else if (readByte == 'z'){
        prop_gems_state = toggle(prop_gems_state);
        digitalWrite(PROP_GEMS, prop_gems_state);
        Serial.print("Toggled PROP Gems: ");
        Serial.println(prop_gems_state);
      }
    }

//    if (millis() - currTime2 >= 1000) {
//       Serial.println("beans!"); 
//       currTime2 = millis();
//    }
  
    readData();
  
    convertData();
    
    //need some check on magnitude of reading to see if we should print data.
    if(shouldPrint){
      if(numLowPressure >= 1){
        Serial.print(convertedLow1);
        //Serial.println("Added first low PT reading; 
      }
      if(numLowPressure >= 2){
        //sprintf(toWriteBuffer + bufferIndex, "%d,", convertedLow2);
        //bufferIndex += String(convertedLow2).length();
        Serial.print(", ");
        Serial.print(convertedLow2);
      }
      if(numLowPressure >= 3){
        //sprintf(toWriteBuffer + bufferIndex, "%d,", convertedLow3);
        //bufferIndex += String(convertedLow3).length();
        Serial.print(", ");
        Serial.print(convertedLow3);
      }
      if(numLowPressure >= 4){
        //sprintf(toWriteBuffer + bufferIndex, "%d,", convertedLow4);
        //bufferIndex += String(convertedLow4).length();
        Serial.print(", ");
        Serial.print(convertedLow4);
      }

      if(numHighPressure >= 1){
        //sprintf(toWriteBuffer + bufferIndex, "%d,", convertedHigh1);
        //bufferIndex += String(convertedHigh1).length();
        Serial.print(", ");
        Serial.print(convertedHigh1);
      }
      if(numHighPressure >= 2){
        //sprintf(toWriteBuffer + bufferIndex, "%d,", convertedHigh2);
        //bufferIndex += String(convertedHigh2).length();
        Serial.print(", ");
        Serial.print(convertedHigh2);
      }
      Serial.print("\n");
      
      //String toWrite = String(converted_inject_low)+','+String(converted_prop_low); // +','+String(converted_prop_high); //+','+String(converted_high_prop);
      //Serial.println(toWriteBuffer);
    }
  }
}

void convertData(){
    switch(numLowPressure){
    case 1:
      convertedLow1 = lowPressureConversion(lowPressure1);
      break;
    case 2:
      convertedLow1 = lowPressureConversion(lowPressure1);
      convertedLow2 = lowPressureConversion(lowPressure2);
      break;
    case 3:
      convertedLow1 = lowPressureConversion(lowPressure1);
      convertedLow2 = lowPressureConversion(lowPressure2);
      convertedLow3 = lowPressureConversion(lowPressure3);
      break;
    case 4:
      convertedLow1 = lowPressureConversion(lowPressure1);
      convertedLow2 = lowPressureConversion(lowPressure2);
      convertedLow3 = lowPressureConversion(lowPressure3);
      convertedLow4 = lowPressureConversion(lowPressure4);
      break;
  }

  switch(numHighPressure){
    case 1:
      convertedHigh1 = highPressureConversion(highPressure1);
      break;
    case 2:
      convertedHigh1 = highPressureConversion(highPressure1);
      convertedHigh2 = highPressureConversion(highPressure2);
      break;
  }
}

void readData(){
  switch(numLowPressure){
    case 1:
      lowPressure1 = analogRead(LOW_PRESSURE_1);
      break;
    case 2:
      lowPressure1 = analogRead(LOW_PRESSURE_1);
      lowPressure2 = analogRead(LOW_PRESSURE_2);
      break;
    case 3:
      lowPressure1 = analogRead(LOW_PRESSURE_1);
      lowPressure2 = analogRead(LOW_PRESSURE_2);
      lowPressure3 = analogRead(LOW_PRESSURE_3);
      break;
    case 4:
      lowPressure1 = analogRead(LOW_PRESSURE_1);
      lowPressure2 = analogRead(LOW_PRESSURE_2);
      lowPressure3 = analogRead(LOW_PRESSURE_3);
      lowPressure4 = analogRead(LOW_PRESSURE_4);
      break;
  }

  switch(numHighPressure){
    case 1:
      highPressure1 = analogRead(HIGH_PRESSURE_1);
      break;
    case 2:
      highPressure1 = analogRead(HIGH_PRESSURE_1);
      highPressure2 = analogRead(HIGH_PRESSURE_2);
      break;
  }
}

float lowPressureConversion(int raw){
  return int(1.2258857538273733*raw - 123.89876445934394);
}

float highPressureConversion(int raw){
  return ((((float)raw * .6949) / 1024) * 4.8 - 1.3) * (5000/3.5) +200;
}

int toggle(int input_state){
  if(input_state == LOW){
     input_state = HIGH;
  } else if (input_state == HIGH){
     input_state = LOW;
  }
  return input_state;
}