type TickerCallback = (data: { price: number; symbol: string; time: number }) => void;

class BinanceWebsocketService {
  private ws: WebSocket | null = null;
  private callbacks: Map<string, Set<TickerCallback>> = new Map();
  private subscribedStreams: Set<string> = new Set();

  public subscribe(symbol: string, callback: TickerCallback) {
    const sym = symbol.toLowerCase();
    const stream = `${sym}@ticker`;

    if (!this.callbacks.has(sym)) {
      this.callbacks.set(sym, new Set());
    }
    this.callbacks.get(sym)!.add(callback);

    if (!this.subscribedStreams.has(stream)) {
      this.subscribedStreams.add(stream);
      this.connect();
    }
  }

  public unsubscribe(symbol: string, callback: TickerCallback) {
    const sym = symbol.toLowerCase();
    const callbacksSet = this.callbacks.get(sym);
    if (callbacksSet) {
      callbacksSet.delete(callback);
      if (callbacksSet.size === 0) {
        this.callbacks.delete(sym);
        const stream = `${sym}@ticker`;
        this.subscribedStreams.delete(stream);
        this.connect(); // reconnect to update streams
      }
    }
  }

  private connect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    if (this.subscribedStreams.size === 0) return;

    const streamsArray = Array.from(this.subscribedStreams);
    const wsUrl = `wss://stream.binance.com:9443/ws/${streamsArray.join("/")}`;

    console.log(`Connecting to Binance WebSocket: ${wsUrl}`);
    this.ws = new WebSocket(wsUrl);

    this.ws.onmessage = (event) => {
      try {
        const raw = JSON.parse(event.data);
        const symbol = raw.s; // e.g. "BTCUSDT"
        const price = parseFloat(raw.c); // current close price
        const time = raw.E; // event time

        if (symbol && price) {
          const callbacksSet = this.callbacks.get(symbol.toLowerCase());
          if (callbacksSet) {
            callbacksSet.forEach((cb) => cb({ price, symbol, time }));
          }
        }
      } catch (err) {
        // quiet fail on websocket parsing noise
      }
    };

    this.ws.onerror = (err) => {
      console.error("Binance WebSocket error:", err);
    };

    this.ws.onclose = () => {
      console.log("Binance WebSocket stream closed.");
      // reconnect helper logic if still has subscriptions
      if (this.subscribedStreams.size > 0) {
        setTimeout(() => this.connect(), 5000);
      }
    };
  }
}

export const binanceWS = new BinanceWebsocketService();
