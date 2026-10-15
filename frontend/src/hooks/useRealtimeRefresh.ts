import { useEffect, useRef, useState } from 'react';
import type { RealtimeChannel } from '@supabase/supabase-js';
import { supabase } from '../api/supabase';

type Listener = {
    onPing: () => void;
    onStatus: (isConnected: boolean) => void;
};

type SharedChannel = {
    channel: RealtimeChannel;
    listeners: Set<Listener>;
    isConnected: boolean;
};

// ONE CHANNEL PER TOPIC, SHARED BY EVERY MOUNTED LISTENER (supabase-js HANDS BACK THE SAME CHANNEL
// FOR A REPEATED TOPIC, AND IT CAN'T TAKE NEW HANDLERS ONCE SUBSCRIBED)
const _channels = new Map<string, SharedChannel>();

function join(topic: string, event: string, listener: Listener): () => void {
    let shared = _channels.get(topic);
    if (!shared) {
        const created: SharedChannel = { channel: supabase.channel(topic), listeners: new Set(), isConnected: false };
        created.channel
            .on('broadcast', { event }, () => created.listeners.forEach(l => l.onPing()))
            .subscribe(status => {
                created.isConnected = status === 'SUBSCRIBED';
                created.listeners.forEach(l => l.onStatus(created.isConnected));
            });
        _channels.set(topic, created);
        shared = created;
    }
    shared.listeners.add(listener);
    listener.onStatus(shared.isConnected);

    const joined = shared;
    return () => {
        joined.listeners.delete(listener);
        if (joined.listeners.size > 0) return;
        _channels.delete(topic);
        supabase.removeChannel(joined.channel);
    };
}

/**
 * Calls `refresh` whenever the server broadcasts `event` on the Supabase Realtime `topic` - a
 * data-free "something changed" ping, so the data itself still comes through the API. Also
 * refreshes on (re)connecting, catching up on any ping missed while away. No subscription while
 * `topic` is null - pass null to leave the channel (e.g. while the tab is hidden).
 *
 * Returns whether the channel is connected, so callers can poll fast as a fallback when it isn't.
 */
export function useRealtimeRefresh(topic: string | null, event: string, refresh: () => void): boolean {
    const [isConnected, setIsConnected] = useState(false);
    const refreshRef = useRef(refresh);
    useEffect(() => {
        refreshRef.current = refresh;
    }, [refresh]);

    useEffect(() => {
        if (!topic) return;
        let wasConnected: boolean | null = null;
        const leave = join(topic, event, {
            onPing: () => refreshRef.current(),
            onStatus: connected => {
                setIsConnected(connected);
                // A (RE)CONNECT MAY HAVE MISSED PINGS - THE FIRST STATUS IS JUST THE CURRENT STATE
                if (connected && wasConnected === false) refreshRef.current();
                wasConnected = connected;
            },
        });
        return () => {
            leave();
            setIsConnected(false);
        };
    }, [topic, event]);

    return topic !== null && isConnected;
}
