export function LoadingSpinner({
  size = 'md',
  label,
  message,
}: {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  message?: string;
}) {
  const sizes = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' };
  const text = message || label;
  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <div className={`${sizes[size]} border-2 border-csi-border border-t-csi-cyan rounded-full animate-spin`} />
      {text && <p className="text-sm text-gray-500">{text}</p>}
    </div>
  );
}
