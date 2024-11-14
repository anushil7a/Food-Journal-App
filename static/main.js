

document.on

const input = document.getElementById('location')
console.log('main',input)

if (input) {
    input.addEventListener('change',(e)=>{
        console.log('change', e )
        const val = input.value
        const parts = val.split('src="')
        if(parts.length>0){
            let link = parts[1]
            link = link.split('"')[0]
            if(link){
                input.value = link
                console.log('trimmed')
            }
        }
    })
}