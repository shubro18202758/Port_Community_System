import * as signalR from '@microsoft/signalr';
import type { VesselPosition } from '../types';

class VesselTrackingConnection {
  private connection: signalR.HubConnection | null = null;
  private onPositionCallback: ((position: VesselPosition) => void) | null = null;

  async connect(onPosition: (position: VesselPosition) => void): Promise<void> {
    if (this.connection?.state === signalR.HubConnectionState.Connected) {
      return;
    }

    this.onPositionCallback = onPosition;

    this.connection = new signalR.HubConnectionBuilder()
      .withUrl('/hubs/vesseltracking')
      .withAutomaticReconnect([0, 2000, 5000, 10000, 30000])
      .configureLogging(signalR.LogLevel.Warning)
      .build();

    this.connection.on('ReceivePositionUpdate', (position: VesselPosition) => {
      if (this.onPositionCallback) {
        this.onPositionCallback(position);
      }
    });

    this.connection.onreconnecting(() => {
      console.log('SignalR reconnecting...');
    });

    this.connection.onreconnected(() => {
      console.log('SignalR reconnected');
    });

    this.connection.onclose(() => {
      console.log('SignalR connection closed');
    });

    try {
      await this.connection.start();
      console.log('SignalR connected');
    } catch (err) {
      console.error('SignalR connection error:', err);
      throw err;
    }
  }

  async subscribeToPort(portCode: string, boundingBox: { minLat: number; minLon: number; maxLat: number; maxLon: number }): Promise<void> {
    if (this.connection?.state === signalR.HubConnectionState.Connected) {
      await this.connection.invoke('SubscribeToPortArea', portCode, boundingBox.minLat, boundingBox.minLon, boundingBox.maxLat, boundingBox.maxLon);
    }
  }

  async subscribeToVessels(vesselIds: number[]): Promise<void> {
    if (this.connection?.state === signalR.HubConnectionState.Connected) {
      await this.connection.invoke('SubscribeToVessels', vesselIds);
    }
  }

  async disconnect(): Promise<void> {
    if (this.connection) {
      await this.connection.stop();
      this.connection = null;
    }
  }

  get isConnected(): boolean {
    return this.connection?.state === signalR.HubConnectionState.Connected;
  }
}

export const vesselTrackingConnection = new VesselTrackingConnection();
