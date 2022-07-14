;(async () => {
  const bleno = require('noble')

  noble.state = 'poweredOn'
  
  noble.on('stateChange', (state) => {
    console.log(`State changed to ${state}`)
  })
  noble.on('discovered', (peripheral) => {
    console.log(`Discovered peripheral: ${peripheral.advertisement.localName}`)
  })
  noble.on('discovered', (peripheral) => {
    console.log(`Discovered peripheral: ${peripheral.advertisement.localName}`)
  })

  noble.startScanning()
})()