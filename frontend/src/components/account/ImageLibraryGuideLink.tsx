import React from 'react';

export const IMAGE_LIBRARY_GUIDE_URL = 'https://github.com/mgula57/mlb_showdown_card_bot/blob/master/docs/user_image_libraries/README.md';

/** External link to the step-by-step guide for making Google Drive library images. */
export const ImageLibraryGuideLink: React.FC<{ children?: React.ReactNode }> = ({ children = 'Read the full guide' }) => (
    <a
        href={IMAGE_LIBRARY_GUIDE_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="text-tertiary underline cursor-pointer hover:opacity-80"
    >
        {children}
    </a>
);

export default ImageLibraryGuideLink;
