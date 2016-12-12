#include "MicroBit.h"
#include "MicroBitUARTService.h"
#include <string>

MicroBit uBit;
MicroBitI2C i2c = MicroBitI2C(I2C_SDA0, I2C_SCL0);
MicroBitUARTService *uart;

#define Temperature 0xE3
#define Humidity 0xE5
#define address 0x80

MicroBitPin soil(MICROBIT_ID_IO_P0, MICROBIT_PIN_P0, PIN_CAPABILITY_ANALOG);
MicroBitPin light(MICROBIT_ID_IO_P1, MICROBIT_PIN_P1, PIN_CAPABILITY_ANALOG);
MicroBitPin pump(MICROBIT_ID_IO_P2, MICROBIT_PIN_P2, PIN_CAPABILITY_DIGITAL);

MicroBitPin P3(MICROBIT_ID_IO_P3, MICROBIT_PIN_P3, PIN_CAPABILITY_ANALOG);
MicroBitPin P4(MICROBIT_ID_IO_P4, MICROBIT_PIN_P4, PIN_CAPABILITY_ANALOG);

int connected = 0;
int waterUsed = 0;
int waterPerPump = 60; //60mm
int pumpTime = 6000; //ms to turn pump on for

//Function for getting data out of the i2c
int readCommand(uint8_t reg, uint8_t* buffer, int length){
	int result;
	if(buffer == NULL || length <= 0)
		return MICROBIT_INVALID_PARAMETER;

	result = i2c.write(address, (const char *)&reg, 1, true);
	if (result !=0)
		return MICROBIT_I2C_ERROR;

	result = i2c.read(address, (char *)buffer, length);
	if(result !=0)
		return MICROBIT_I2C_ERROR;

	return MICROBIT_OK;
}

//Function for getting roughly how much water was used. ROUGHLY!!!!
string get_waterUsed(){

	char buffer[5];
	snprintf(buffer, 5, "%d", waterUsed);
	char data[20];
	strcpy(data, "10801,");
	strcat(data, buffer);

	return data;
}

//FUnction for checking moisture to target and control pump
bool moistureTarget(ManagedString targetStr){
	int status = false;

	char c = targetStr.charAt(0);
	char d = targetStr.charAt(1);

	int a = c - '0';
	int b = d - '0';
	int target = (a * 10) + b;

	float soilAnalog = soil.getAnalogValue();
	float soilPercent = 100 - soilAnalog / 10.24;

	int soilInt = soilPercent;

	if(soilInt < target){
		pump.setDigitalValue(1);
		uBit.sleep(pumpTime);
		pump.setDigitalValue(0);
		
		waterUsed += waterPerPump;
	}
	
	//Send water used here
	string data = get_waterUsed();
	const char *cstr = data.c_str();
	uart->send(cstr);

	if(connected == 1){
		status = true;
		//uart->send("done");	
	} 

	return status;
}

//Function for getting the soil mositure
string get_soilMoisture(){
	/*********Soil moisture level*********/
	float soilAnalog = soil.getAnalogValue();
	float soilPercent = 100 - soilAnalog / 10.24;

	int soilInt = soilPercent;

	char buffer[5];
	snprintf(buffer, 5, "%d", soilInt);
	char data[20];
	strcpy(data, "10802,");
	strcat(data, buffer);

	return data;
}

//Function get light level
string get_lightLevel(){

	float lightAnalog = light.getAnalogValue();
	float lightPercent = lightAnalog / 10;

	int lightInt = lightPercent;

	char buffer[5];
	snprintf(buffer, 5, "%d", lightInt);
	char data[20];
	strcpy(data, "10803,");
	strcat(data, buffer);

	return data;
}

//Function for getting digital temperature data from i2c 
string get_temperarueI2C(){
	uint8_t temperature[3];

	int result;
	
	result = readCommand(Temperature, (uint8_t *)temperature, 3);
	if(result != 0){
		uBit.display.scroll(MICROBIT_I2C_ERROR);
	}
		
	//Calculating Temperature
	uint16_t tempRaw = (temperature[0] << 8) | temperature[1];
	float rwvTemp = -46.85 + 175.72  * (float(tempRaw)/65536.0);

	int tempInt = rwvTemp;

	char buffer[5];
	snprintf(buffer, 5, "%d", tempInt);
	char data[20];
	strcpy(data, "1424,");
	strcat(data, buffer);

	return data;
}

//Function for getting digital humidity data from i2c 
string get_humidityI2C(){
	uint8_t humidity[3];

	int result;
	
	result = readCommand(Humidity, (uint8_t *)humidity, 3);
	if(result != 0){
		uBit.display.scroll(MICROBIT_I2C_ERROR);
	}
		
	//Calculating Humidity
	result = readCommand(Humidity, (uint8_t *)humidity, 3);
	if(result != 0)
		uBit.display.scroll(MICROBIT_I2C_ERROR);
	
	uint16_t humRaw = (humidity[0] << 8) | humidity[1];
	float rwvHum = -6 + 125 * (float(humRaw)/65536.0);

	int humInt = rwvHum;

	char buffer[5];
	snprintf(buffer, 5, "%d", humInt);
	char data[20];
	strcpy(data, "1024,");
	strcat(data, buffer);

	return data;
}

//Function for getting battery level in volts
//NOTE THIS WONT RETURN BATTERY VOLTAGE LEVEL WHEN PLUGGED IN WITH USB
string get_batteryLevel(){
	float ADCValP3 = P3.getAnalogValue();
	float ADCValP4 = P4.getAnalogValue();
	float vBatt = ((41/39) * ((ADCValP3 * 2.048) / ADCValP4)) * 1000;

	int vBattInt = vBatt; //Volts to milli volts so dont need to do decimal place

	char buffer[5];
	snprintf(buffer, 5, "%d", vBattInt);
	char data[20];
	strcpy(data, "10804,");
	strcat(data, buffer);

	return data;
}


//Function to control data sending over uart
bool uart_sendData(){
	int status = false;

	//Send all sensors except from water used that gets sent from its own function
	string data = "";

	//Soil Moisture
	data = get_soilMoisture();
	const char *moist = data.c_str();
	uart->send(moist);

	//Light Level
	data = get_lightLevel();
	const char *light = data.c_str();
	uart->send(light);

	//Digital Temperature
	data = get_temperarueI2C();
	const char *temp = data.c_str();
	uart->send(temp);

	//Digital Humidity
	data = get_humidityI2C();
	const char *hum = data.c_str();
	uart->send(hum);

	//Battery Level
	data = get_batteryLevel();
	const char *batt = data.c_str();
	uart->send(batt);
	
	if(connected == 1){
		status = true;
		//uart->send("sent");	
	} 

	return status;
}

//When a device connects over ble
void onConnected(MicroBitEvent e)
{
	uBit.display.scroll("C");
	connected = 1;

	ManagedString eom(":");

	while(connected == 1){
		ManagedString msg = uart->readUntil(eom);		
		
		//Check what micro:bit is meant to do
		if(msg == "send"){
			//Check if data was sent succesfully
			if(uart_sendData()){
				uBit.display.scroll("sy");			
			} else {
				uBit.display.scroll("sn");			
			}
		//message contains target for moisture (target=50)
		} else if(msg.substring(0,6) == "target"){
			if(moistureTarget(msg.substring(7,2))){
				uBit.display.scroll("ty");			
			} else {
				uBit.display.scroll("tn");			
			}
		}
	}
}

//When a device disconnectes over ble
void onDisconnected(MicroBitEvent e)
{
	uBit.display.scroll("D");
	connected = 0;
}

int main()
{
	//Init microbit Ubit
	uBit.init();

	//Setup ble services
	uart = new MicroBitUARTService(*uBit.ble, 32, 32); //UART service

	//Listen for ble events for connection
	uBit.messageBus.listen(MICROBIT_ID_BLE, MICROBIT_BLE_EVT_CONNECTED, onConnected);
	uBit.messageBus.listen(MICROBIT_ID_BLE, MICROBIT_BLE_EVT_DISCONNECTED, onDisconnected);

	//Display ready
	uBit.display.scroll("READY");

	release_fiber();
}
