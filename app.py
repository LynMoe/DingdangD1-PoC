import asyncio
from PIL import Image
from bleak import BleakClient

ADDRESS = "1FA49315-821B-5735-4F8D-4958D73E5AD5" # for macOS
# ADDRESS = "55:55:09:F0:2A:74" # for Windows

CHARACTERISTIC = "0000ff02-0000-1000-8000-00805f9b34fb"

# credits to https://www.emexee.com/2022/01/thermal-printer-image-converter.html
# using floyd-steinberg dithering
def applyDither(size, pixels):
    ditherBrightness = 0.35
    ditherContrast = 1.45

    def getValue(pixels, y, x):
        return int((pixels[x, y][0] + pixels[x, y][1] + pixels[x, y][2]) / 3)
    def setValue(pixels, y, x, v):
        pixels[x, y] = (v, v, v)
    def nudgeValue(pixels, y, x, v):
        v = int(v)
        pixels[x, y] = (pixels[x, y][0] + v, pixels[x, y][1] + v, pixels[x, y][2] + v)

    w, h = size
    brightness = float(ditherBrightness)
    contrast = float(ditherContrast) ** 2
    for y in range(h):
        for x in range(w):
            for i in range(3):
                r, g, b = pixels[x, y]
                arr = [r, g, b]
                arr[i] += (brightness - 0.5) * 256
                arr[i] = (arr[i] - 128) * contrast + 128
                arr[i] = int(min(max(arr[i], 0), 255))
                pixels[x, y] = (arr[0], arr[1], arr[2])

    for y in range(h):
        BOTTOM_ROW = y == h - 1
        for x in range(w):
            LEFT_EDGE = x == 0
            RIGHT_EDGE = x == w - 1
            i = (y * w + x) * 4
            level = getValue(pixels, y, x)
            newLevel = (level < 128) * 0 + (level >= 128) * 255
            setValue(pixels, y, x, newLevel)
            error = level - newLevel
            if not RIGHT_EDGE:
                nudgeValue(pixels, y, x + 1, error * 7 / 16)
            if not BOTTOM_ROW and not LEFT_EDGE:
                nudgeValue(pixels, y + 1, x - 1, error * 3 / 16)
            if not BOTTOM_ROW:
                nudgeValue(pixels, y + 1, x, error * 5 / 16)
            if not BOTTOM_ROW and not RIGHT_EDGE:
                nudgeValue(pixels, y + 1, x + 1, error * 1 / 16)

imgBinStr = ''
width = 384

img = Image.open("cat.jpg")
img = img.convert("RGB")
img = img.resize((width, int(img.height * width / img.width)), Image.LANCZOS)
pixels = img.load()
applyDither(img.size, pixels)

for y in range(img.size[1]):
    for x in range(img.size[0]):
        r, g, b = pixels[x, y]
        if r + g + b > 600:
            imgBinStr += '0'
        else:
            imgBinStr += '1'

# start bits
imgBinStr = '1' + '0' * 318 + imgBinStr

# convert to hex
imgHexStr = hex(int(imgBinStr, 2))[2:]

def notification_handler(sender, data):
    print("0x{0}: {1}".format(sender, data))
    # exit when complete
    if (data == b'\xaa'):
        exit()

async def main():
    async with BleakClient(ADDRESS) as client:
        # subscribe notifications
        await client.start_notify('0000ff01-0000-1000-8000-00805f9b34fb', notification_handler)
        await client.start_notify('0000ff03-0000-1000-8000-00805f9b34fb', notification_handler)
        await asyncio.sleep(0.2)

        # enable the printer(for model D1)
        await client.write_gatt_char(CHARACTERISTIC, bytes.fromhex('10FF40'))
        await client.write_gatt_char(CHARACTERISTIC, bytes.fromhex('10FFF103'))

        # set density (0000 for low, 0100 for normal, 0200 for high)
        await client.write_gatt_char(CHARACTERISTIC, bytes.fromhex('10FF10000200'.ljust(256, '0')))
        
        # no need(maybe)
        for i in range(4):
            await client.write_gatt_char(CHARACTERISTIC, bytes.fromhex(''.ljust(256, '0')))

        # magic number (a simple guess :D
        hexlen = hex(int(len(imgHexStr) / 96) + 3)[2:]

        # little-endian for the length of hex lines
        fronthex = hexlen
        endhex = '0'
        if (len(hexlen) > 2):
            fronthex = hexlen[1:3]
            endhex += hexlen[0:1]
        else:
            endhex += '0'
        # start command with data length
        await client.write_gatt_char(CHARACTERISTIC, bytes.fromhex(('1D7630003000' + fronthex + endhex).ljust(32, '0') + imgHexStr[0:224]))
        await asyncio.sleep(0.05)

        # send the image data in chunks
        for i in range(32 * 7, len(imgHexStr), 256):
            str = imgHexStr[i:i + 256]
            if (len(str) < 256):
                str = str.ljust(256, '0')
            await client.write_gatt_char(CHARACTERISTIC, bytes.fromhex(str))
            await asyncio.sleep(0.035)

        # end signal
        await client.write_gatt_char(CHARACTERISTIC, bytes.fromhex('1B4A64'.rjust(256, '0')))
        await client.write_gatt_char(CHARACTERISTIC, bytes.fromhex('10FFF145'))

        # wait for the complete notification
        await asyncio.sleep(6)

if __name__ == "__main__":
    asyncio.run(main())
