import React, { useState, useCallback } from 'react';
import Cropper, { type Area } from 'react-easy-crop';
import { FaSpinner } from 'react-icons/fa';

import { buttonClass } from '../shared/buttonStyles';
import { Heading } from '../shared/Heading';
interface AvatarCropModalProps {
    imageSrc: string;
    onApply: (blob: Blob) => void;
    onCancel: () => void;
    isUploading: boolean;
}

async function getCroppedBlob(imageSrc: string, pixelCrop: Area): Promise<Blob | null> {
    const image = await new Promise<HTMLImageElement>((resolve, reject) => {
        const img = new Image();
        img.addEventListener('load', () => resolve(img));
        img.addEventListener('error', reject);
        img.src = imageSrc;
    });

    const canvas = document.createElement('canvas');
    canvas.width = pixelCrop.width;
    canvas.height = pixelCrop.height;
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    ctx.drawImage(
        image,
        pixelCrop.x, pixelCrop.y,
        pixelCrop.width, pixelCrop.height,
        0, 0,
        pixelCrop.width, pixelCrop.height,
    );

    return new Promise(resolve => canvas.toBlob(b => resolve(b), 'image/jpeg', 0.9));
}

const AvatarCropModal: React.FC<AvatarCropModalProps> = ({ imageSrc, onApply, onCancel, isUploading }) => {
    const [crop, setCrop] = useState({ x: 0, y: 0 });
    const [zoom, setZoom] = useState(1);
    const [croppedAreaPixels, setCroppedAreaPixels] = useState<Area | null>(null);

    const onCropComplete = useCallback((_: Area, pixels: Area) => {
        setCroppedAreaPixels(pixels);
    }, []);

    const handleApply = async () => {
        if (!croppedAreaPixels) return;
        const blob = await getCroppedBlob(imageSrc, croppedAreaPixels);
        if (blob) onApply(blob);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
            <div className="bg-(--background-secondary) rounded-card shadow-overlay w-full max-w-md mx-4 overflow-hidden">
                <div className="px-5 py-4 border-b border-form-element">
                    <Heading level="section">Crop Photo</Heading>
                    <p className="text-xs text-secondary mt-0.5">Drag to reposition · scroll or pinch to zoom</p>
                </div>

                {/* Crop area */}
                <div className="relative w-full" style={{ height: 320 }}>
                    <Cropper
                        image={imageSrc}
                        crop={crop}
                        zoom={zoom}
                        aspect={1}
                        cropShape="round"
                        showGrid={false}
                        onCropChange={setCrop}
                        onZoomChange={setZoom}
                        onCropComplete={onCropComplete}
                    />
                </div>

                {/* Zoom slider */}
                <div className="px-5 py-3 border-t border-form-element">
                    <input
                        type="range"
                        min={1}
                        max={3}
                        step={0.01}
                        value={zoom}
                        onChange={e => setZoom(Number(e.target.value))}
                        className="w-full accent-(--showdown-blue)"
                        aria-label="Zoom"
                    />
                </div>

                {/* Actions */}
                <div className="px-5 py-4 border-t border-form-element flex justify-end gap-3">
                    <button
                        type="button"
                        onClick={onCancel}
                        disabled={isUploading}
                        className={buttonClass('secondary')}
                    >
                        Cancel
                    </button>
                    <button
                        type="button"
                        onClick={handleApply}
                        disabled={isUploading}
                        className={buttonClass('primary')}
                    >
                        {isUploading && <FaSpinner className="w-3.5 h-3.5 animate-spin" />}
                        {isUploading ? 'Saving…' : 'Apply'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AvatarCropModal;
