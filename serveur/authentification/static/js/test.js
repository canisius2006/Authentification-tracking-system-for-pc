// Nous allons faire du fetching des données bg 

async function avoir(){
    const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg2NDQ0NDA2LCJpYXQiOjE3ODY0NDI2MDYsImp0aSI6IjgyOTM5MmVmZjc1ZTRhMzVhOGQ5ZjdjN2VmMjFlOWNkIiwidXNlcl9pZCI6IjEifQ.1YDlCPtFrQyogS7kYKeBPSmJMCRhQKDtx5CWdDlcF8I"
    data = await fetch('http://127.0.0.1:8000/api/application/',
        {
            method:"POST",
            headers:{
                'Authorization':`Bearer ${token}`,
                'Content-Type':'application/json'
                
            },
            body:JSON.stringify({
                session:1,
                nom:JSON.stringify({"application": "chrome.exe", "titre": "(3) Redbone - Come and Get Your Love (Single Edit - Audio) - YouTube - Google Chrome"})
            })
        }
    )
    console.log(data)
    console.log(data.JSON)
}

avoir()