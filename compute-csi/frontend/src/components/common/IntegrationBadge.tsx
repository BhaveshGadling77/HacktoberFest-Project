interface Props {
  connected: boolean | undefined;
  label?: string;
}

export function IntegrationBadge({ connected, label }: Props) {
  if (connected === undefined) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-gray-500">
        <span className="w-2 h-2 rounded-full bg-gray-600" />
        {label ?? 'Unknown'}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1.5 text-xs ${connected ? 'text-green-400' : 'text-red-400'}`}>
      <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400 animate-pulse' : 'bg-red-500'}`} />
      {label ?? (connected ? 'Connected' : 'Disconnected')}
    </span>
  );
}
