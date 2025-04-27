from js import Response

async def on_fetch(request, env):
    try:
        if request.method == "POST" and request.url.endswith("/api/chat"):
            data = await request.json()
            return Response.new(
                JSON.stringify({
                    "response": f"Echo: {data.get('message', 'No message provided')}"
                }),
                {
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "POST, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type"
                    }
                }
            )
        elif request.method == "OPTIONS":
            return Response.new(
                None,
                {
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "POST, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type"
                    }
                }
            )
        else:
            return Response.new("Not Found", {"status": 404})
    except Exception as e:
        return Response.new(
            JSON.stringify({"error": str(e)}),
            {
                "status": 500,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            }
        ) 