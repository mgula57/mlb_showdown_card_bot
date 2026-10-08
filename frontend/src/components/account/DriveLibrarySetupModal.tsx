/**
 * @fileoverview Drive Library Setup Modal
 *
 * Walks a user through connecting a Google Drive folder as an image library:
 * 1. Prepare the folder (naming convention)
 * 2. Share it (Viewer) with the Showdown Bot service account
 * 3. Paste the link, test the connection, and save
 */

import React, { useState } from 'react';
import { FaCheck, FaCheckCircle, FaCopy, FaExclamationTriangle, FaSpinner } from 'react-icons/fa';
import { Modal } from '../shared/Modal';
import { imageForSet } from '../shared/SiteSettingsContext';
import FormInput from '../customs/FormInput';
import ImageLibraryGuideLink from './ImageLibraryGuideLink';
import { saveImageLibrary, testImageLibrary } from '../../api/imageLibraries';
import type { ImageLibrariesOverview, ImageLibraryTestResult } from '../../api/imageLibraries';

type DriveLibrarySetupModalProps = {
    token: string;
    serviceAccountEmail: string;
    onClose: () => void;
    onSaved: (overview: ImageLibrariesOverview) => void;
};

const STEPS = ['Prepare folder', 'Share with bot', 'Connect & test'];

const EXAMPLE_FILE_NAME = 'BG-2001-Bonds-(bondsba01)-(SFG).png';

/** Which image types each set uses. Keep in sync with Set.player_image_components_list in sets.py. */
const SET_IMAGE_REQUIREMENTS: { sets: string[]; files: string }[] = [
    { sets: ['2000', '2001'], files: 'CUT' },
    { sets: ['2002', '2003', '2004', '2005'], files: 'BG' },
    { sets: ['CLASSIC', 'EXPANDED'], files: 'BG + CUT' },
];

const buttonBase = 'px-4 py-2 rounded-lg text-sm font-semibold cursor-pointer disabled:cursor-not-allowed disabled:opacity-50 transition-colors';
const primaryButton = `${buttonBase} bg-accent text-primary hover:opacity-90`;
const secondaryButton = `${buttonBase} border border-form-element text-secondary hover:bg-background-tertiary`;

const Code: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <code className="px-1.5 py-0.5 rounded bg-background-tertiary text-secondary text-[13px] break-all">{children}</code>
);

const StepList: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <ol className="list-decimal pl-5 space-y-2 text-sm text-secondary">{children}</ol>
);

const Note: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <p className="text-xs text-gray-500">{children}</p>
);

/** Step indicator across the top of the modal. */
const StepIndicator: React.FC<{ step: number }> = ({ step }) => (
    <div className="flex items-center gap-2 mb-5">
        {STEPS.map((label, index) => {
            const isDone = index < step;
            const isActive = index === step;
            return (
                <React.Fragment key={label}>
                    {index > 0 && <div className={`flex-1 h-px ${isDone || isActive ? 'bg-accent' : 'bg-form-element'}`} />}
                    <div className="flex items-center gap-1.5 shrink-0">
                        <span className={`
                            w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
                            ${isDone || isActive ? 'bg-accent text-primary border border-form-element' : 'border border-form-element text-gray-500'}
                        `}>
                            {isDone ? <FaCheck className="w-2.5 h-2.5" /> : index + 1}
                        </span>
                        <span className={`text-xs hidden sm:inline ${isActive ? 'text-secondary font-semibold' : 'text-gray-500'}`}>{label}</span>
                    </div>
                </React.Fragment>
            );
        })}
    </div>
);

/** Copyable service account email. */
const CopyableEmail: React.FC<{ email: string }> = ({ email }) => {
    const [copied, setCopied] = useState(false);
    const copy = () => {
        navigator.clipboard?.writeText(email).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
        }).catch(() => {});
    };
    return (
        <div className="flex items-center gap-2 rounded-lg border border-form-element bg-background-primary px-3 py-2">
            <span className="flex-1 text-sm text-secondary font-mono break-all">{email}</span>
            <button type="button" onClick={copy} className="shrink-0 flex items-center gap-1 text-xs text-tertiary cursor-pointer hover:underline">
                {copied ? <FaCheck /> : <FaCopy />}
                {copied ? 'Copied' : 'Copy'}
            </button>
        </div>
    );
};

/** Result of a connection test. */
export const ImageLibraryTestResultPanel: React.FC<{ result: ImageLibraryTestResult }> = ({ result }) => {
    const unrecognizedCount = result.image_count - result.recognized_image_count;
    const hasNoMatches = result.recognized_image_count === 0;
    return (
        <div className="rounded-lg border border-green-600/40 bg-green-600/10 p-4 space-y-2">
            <p className="flex items-center gap-2 text-sm font-semibold text-secondary">
                <FaCheckCircle className="text-green-500" />
                Connected to “{result.name}”
            </p>
            <ul className="text-sm text-secondary space-y-1 pl-6">
                <li>{result.image_count} image{result.image_count === 1 ? '' : 's'} found</li>
                <li>{result.recognized_image_count} follow the naming format</li>
                {result.other_file_count > 0 && <li className="text-gray-500">{result.other_file_count} non-image file{result.other_file_count === 1 ? '' : 's'} will be ignored</li>}
            </ul>
            {unrecognizedCount > 0 && (
                <div className="flex gap-2 text-xs text-yellow-500 pt-1">
                    <FaExclamationTriangle className="shrink-0 mt-0.5" />
                    <div>
                        <p>{unrecognizedCount} image{unrecognizedCount === 1 ? " doesn't" : "s don't"} match the naming format and won't be used, for example:</p>
                        <ul className="mt-1 space-y-0.5">
                            {result.unrecognized_examples.map(name => <li key={name}><Code>{name}</Code></li>)}
                        </ul>
                    </div>
                </div>
            )}
            {hasNoMatches && (
                <Note>You can still save this folder and add correctly named images later. They're picked up automatically.</Note>
            )}
        </div>
    );
};

const ErrorPanel: React.FC<{ message: string }> = ({ message }) => (
    <div className="flex gap-2 rounded-lg border border-red-600/40 bg-red-600/10 p-4 text-sm text-secondary">
        <FaExclamationTriangle className="text-red-500 shrink-0 mt-0.5" />
        <p>{message}</p>
    </div>
);

export const DriveLibrarySetupModal: React.FC<DriveLibrarySetupModalProps> = ({ token, serviceAccountEmail, onClose, onSaved }) => {
    const [step, setStep] = useState(0);
    const [folder, setFolder] = useState('');
    const [testedFolder, setTestedFolder] = useState<string | null>(null);
    const [testResult, setTestResult] = useState<ImageLibraryTestResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isTesting, setIsTesting] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    // Saving is only allowed for the exact link that passed the test
    const canSave = !!testResult && testedFolder === folder.trim() && !isSaving;

    const handleFolderChange = (value: string | null) => {
        setFolder(value ?? '');
        setError(null);
    };

    const handleTest = async () => {
        setIsTesting(true);
        setError(null);
        setTestResult(null);
        try {
            const result = await testImageLibrary(token, folder.trim());
            setTestResult(result);
            setTestedFolder(folder.trim());
        } catch (err) {
            setError((err as Error).message);
        } finally {
            setIsTesting(false);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        setError(null);
        try {
            const overview = await saveImageLibrary(token, folder.trim());
            onSaved(overview);
            onClose();
        } catch (err) {
            setError((err as Error).message);
            setIsSaving(false);
        }
    };

    const footer = (
        <div className="flex justify-between gap-2">
            <button type="button" className={secondaryButton} onClick={step === 0 ? onClose : () => setStep(step - 1)}>
                {step === 0 ? 'Cancel' : 'Back'}
            </button>
            {step < STEPS.length - 1 ? (
                <button type="button" className={primaryButton} onClick={() => setStep(step + 1)}>Next</button>
            ) : (
                <button type="button" className={primaryButton} onClick={handleSave} disabled={!canSave}>
                    {isSaving ? 'Saving…' : 'Save library'}
                </button>
            )}
        </div>
    );

    return (
        <Modal
            title="Connect a Google Drive folder"
            subtitle="Use your own player images for Auto card images"
            size="md"
            onClose={onClose}
            footer={footer}
        >
            <div className="p-4">
                <StepIndicator step={step} />

                {step === 0 && (
                    <div className="space-y-4">
                        <p className="text-sm text-secondary">
                            New to making player images? <ImageLibraryGuideLink>Read the full guide</ImageLibraryGuideLink> for templates, canvas setup, and examples.
                        </p>
                        <StepList>
                            <li>
                                Create a folder in Google Drive. Any Google account works. Work or school accounts may block sharing outside the organization, so a personal account is best.
                            </li>
                            <li>
                                Add your player images directly to the folder (subfolders aren't searched), named like:
                                <div className="mt-1.5"><Code>{EXAMPLE_FILE_NAME}</Code></div>
                            </li>
                        </StepList>

                        <div className="rounded-lg border border-form-element p-3 space-y-2 text-sm text-secondary">
                            <div className="justify-between flex">
                                <p className="font-semibold">Naming format</p>
                                <span className="font-extrabold text-(--warning)">**IMPORTANT**</span>
                            </div>
                            <p><Code>{'{TYPE}-{YEAR}-{NAME}-({PLAYER ID})-({TEAM}).png'}</Code></p>
                            <ul className="space-y-1 text-xs">
                                <li><b>TYPE</b>: <Code>BG</Code> for a full player image with the background included, <Code>CUT</Code> for a cutout of the player on a transparent background.</li>
                                <li><b>YEAR</b>: the season the image is from. When a player has several images, the one closest to the card's year is used.</li>
                                <li><b>NAME</b>: doesn't need to match anything. It's only there to keep your folder organized.</li>
                                <li><b>PLAYER ID</b> (most important): how images are matched to players, so it must be exact. Use the Baseball Reference ID (ex: <Code>bondsba01</Code> from baseball-reference.com/players/b/bondsba01.shtml) or the MLB ID (ex: <Code>111188</Code> from mlb.com/player/barry-bonds-111188).</li>
                                <li><b>TEAM</b> (optional, recommended): the <b>Baseball Reference</b> team ID (ex: <Code>SFG</Code>, not SF), as seen in team page URLs like baseball-reference.com/teams/SFG/2001.shtml. Helps pick the right image when a player has several.</li>
                                <li><b>Other options</b> (optional): add any of these in parentheses after the team to target specific cards:
                                    <ul className="mt-1 space-y-0.5 pl-3">
                                        <li><Code>(POST)</Code> postseason cards</li>
                                        <li><Code>(DARK)</Code> dark mode cards</li>
                                        <li><Code>(HITTER)</Code> or <Code>(PITCHER)</Code> two-way players (ex: Ohtani)</li>
                                    </ul>
                                </li>
                            </ul>
                        </div>

                        <div className="rounded-lg border border-form-element p-3 space-y-2 text-sm text-secondary">
                            <p className="font-semibold">Image size</p>
                            <ul className="space-y-1 text-xs">
                                <li><b>Aspect ratio</b>: 5:7 (portrait), the same shape as the card. Other shapes are center-cropped to fit.</li>
                                <li><b>Size</b>: <Code>1500 x 2100</Code> px recommended. Smaller images are scaled up and may look blurry.</li>
                                <li><b>Format</b>: PNG recommended (JPG works for <Code>BG</Code>). <Code>CUT</Code> images must be PNG with a transparent background.</li>
                                <li><b>Shown as is</b>: the image is placed on the card just like an uploaded image, on every set. Use <Code>1644 x 2244</Code> px to also fill the border on bordered cards.</li>
                            </ul>
                            <Note>Want each set to position your image like the Showdown Bot library does? Use exactly <Code>1950 x 2730</Code> px with the 1500 x 2100 card area centered. Each set crops, zooms, and shifts it to fit its design.</Note>
                        </div>

                        <div className="rounded-lg border border-form-element p-3 text-sm text-secondary">
                            <p className="font-semibold mb-2">Images each set needs</p>
                            <table className="w-full text-xs">
                                <tbody>
                                    {SET_IMAGE_REQUIREMENTS.map(row => (
                                        <tr key={row.files} className="border-t border-form-element first:border-t-0">
                                            <td className="py-2 pr-3">
                                                <div className="flex flex-wrap items-center gap-2">
                                                    {row.sets.map(set => (
                                                        <img
                                                            key={set}
                                                            src={imageForSet(set)}
                                                            alt={set}
                                                            title={set}
                                                            className="h-6 w-14 object-contain object-left"
                                                        />
                                                    ))}
                                                </div>
                                            </td>
                                            <td className="py-2 font-semibold whitespace-nowrap text-right">{row.files}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            <div className="flex gap-2 rounded-md bg-background-tertiary p-2 my-2 text-xs">
                                <FaExclamationTriangle className="shrink-0 mt-0.5 text-yellow-500" />
                                <p>
                                    Special editions like <b>Super Season</b> and <b>Cooperstown Collection</b>, plus <b>parallels</b> (Rainbow Foil, Gold, Moonlight, etc.), need <b>both BG and CUT</b> images, even on sets that normally use just one. Add both for a player to cover every option.
                                </p>
                            </div>
                            <Note>A player only matches when every image type the card needs is in the folder. Otherwise the next library in your search order is used.</Note>
                        </div>
                    </div>
                )}

                {step === 1 && (
                    <div className="space-y-4">
                        <StepList>
                            <li>In Google Drive, right-click your folder and choose <b>Share</b>.</li>
                            <li>
                                Add this email:
                                <div className="mt-1.5"><CopyableEmail email={serviceAccountEmail} /></div>
                            </li>
                            <li>Set the role to <b>Viewer</b>. Folders shared with edit access are rejected.</li>
                            <li>Uncheck <b>Notify people</b>, then click <b>Share</b>.</li>
                        </StepList>
                        <Note>
                            Showdown Bot can only see this one folder, and can't change anything in it. To revoke access at any time, remove the email from the folder's sharing settings in Google Drive.
                        </Note>
                    </div>
                )}

                {step === 2 && (
                    <div className="space-y-4">
                        <FormInput
                            label="Folder link"
                            value={folder}
                            onChange={handleFolderChange}
                            isClearable={true}
                            inputMode="url"
                            placeholder="https://drive.google.com/drive/folders/..."
                        />
                        <button
                            type="button"
                            className={`${secondaryButton} flex items-center gap-2`}
                            onClick={handleTest}
                            disabled={!folder.trim() || isTesting}
                        >
                            {isTesting && <FaSpinner className="animate-spin" />}
                            {isTesting ? 'Testing…' : 'Test connection'}
                        </button>

                        {isTesting && <div className="h-28 rounded-lg bg-background-tertiary animate-pulse" />}
                        {!isTesting && testResult && testedFolder === folder.trim() && <ImageLibraryTestResultPanel result={testResult} />}
                        {!isTesting && error && <ErrorPanel message={error} />}
                    </div>
                )}
            </div>
        </Modal>
    );
};

export default DriveLibrarySetupModal;
