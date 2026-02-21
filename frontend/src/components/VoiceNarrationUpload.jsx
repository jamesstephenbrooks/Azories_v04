import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { FiMic, FiUpload, FiTrash2, FiPlay, FiPause, FiCheck, FiX } from 'react-icons/fi';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

export default function VoiceNarrationUpload({ bookId, pages = [], onNarrationUpdate }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const [recordings, setRecordings] = useState({});
  const [isPlaying, setIsPlaying] = useState(null);
  const [uploadProgress, setUploadProgress] = useState({});
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioRef = useRef(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        audioChunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const audioUrl = URL.createObjectURL(audioBlob);
        
        setRecordings(prev => ({
          ...prev,
          [currentPageIndex]: {
            blob: audioBlob,
            url: audioUrl,
            uploaded: false
          }
        }));
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      toast.error('Could not access microphone. Please allow microphone access.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const playRecording = (pageIndex) => {
    const recording = recordings[pageIndex];
    if (!recording) return;

    if (isPlaying === pageIndex) {
      audioRef.current?.pause();
      setIsPlaying(null);
    } else {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      audioRef.current = new Audio(recording.url);
      audioRef.current.onended = () => setIsPlaying(null);
      audioRef.current.play();
      setIsPlaying(pageIndex);
    }
  };

  const deleteRecording = (pageIndex) => {
    if (recordings[pageIndex]?.url) {
      URL.revokeObjectURL(recordings[pageIndex].url);
    }
    setRecordings(prev => {
      const newRecordings = { ...prev };
      delete newRecordings[pageIndex];
      return newRecordings;
    });
  };

  const uploadRecording = async (pageIndex) => {
    const recording = recordings[pageIndex];
    if (!recording || recording.uploaded) return;

    const formData = new FormData();
    formData.append('audio', recording.blob, `page_${pageIndex}_narration.webm`);
    formData.append('page_index', pageIndex.toString());

    try {
      setUploadProgress(prev => ({ ...prev, [pageIndex]: 0 }));
      
      const response = await axios.post(
        `${API}/api/books/${bookId}/narration/${pageIndex}`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(prev => ({ ...prev, [pageIndex]: percent }));
          }
        }
      );

      setRecordings(prev => ({
        ...prev,
        [pageIndex]: { ...prev[pageIndex], uploaded: true, serverUrl: response.data.audio_url }
      }));

      toast.success(`Narration for page ${pageIndex + 1} uploaded!`);
      if (onNarrationUpdate) onNarrationUpdate();
    } catch (error) {
      toast.error('Failed to upload narration');
    } finally {
      setUploadProgress(prev => {
        const newProgress = { ...prev };
        delete newProgress[pageIndex];
        return newProgress;
      });
    }
  };

  const uploadAllRecordings = async () => {
    const unuploadedPages = Object.entries(recordings)
      .filter(([_, r]) => !r.uploaded)
      .map(([pageIndex]) => parseInt(pageIndex));

    for (const pageIndex of unuploadedPages) {
      await uploadRecording(pageIndex);
    }
  };

  const currentPage = pages[currentPageIndex];
  const hasUnuploadedRecordings = Object.values(recordings).some(r => !r.uploaded);

  return (
    <>
      {/* Trigger Button */}
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(true)}
        className="gap-2"
        data-testid="voice-narration-trigger"
      >
        <FiMic className="w-4 h-4" />
        Record Narration
      </Button>

      {/* Modal */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
            onClick={() => setIsOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="bg-background rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden"
              onClick={e => e.stopPropagation()}
            >
              {/* Header */}
              <div className="p-4 border-b flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-red-500/10 rounded-full flex items-center justify-center">
                    <FiMic className="w-5 h-5 text-red-500" />
                  </div>
                  <div>
                    <h2 className="font-bold">Record Your Narration</h2>
                    <p className="text-xs text-muted-foreground">Add your voice to the story</p>
                  </div>
                </div>
                <button onClick={() => setIsOpen(false)} className="p-2 hover:bg-muted rounded-full">
                  <FiX className="w-5 h-5" />
                </button>
              </div>

              <div className="p-4 space-y-4">
                {/* Page Navigation */}
                <div className="flex items-center gap-2 overflow-x-auto pb-2">
                  {pages.map((page, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentPageIndex(index)}
                      className={`flex-shrink-0 px-3 py-2 rounded-lg text-sm transition-colors ${
                        currentPageIndex === index
                          ? 'bg-primary text-primary-foreground'
                          : recordings[index]
                            ? 'bg-green-500/10 text-green-500 border border-green-500/20'
                            : 'bg-muted hover:bg-muted/80'
                      }`}
                    >
                      {recordings[index] && <FiCheck className="w-3 h-3 mr-1 inline" />}
                      Page {index + 1}
                    </button>
                  ))}
                </div>

                {/* Current Page Content */}
                <div className="bg-muted/50 p-4 rounded-xl max-h-40 overflow-y-auto">
                  <p className="text-sm whitespace-pre-wrap">
                    {currentPage?.text || currentPage?.chapter_title || 'No text on this page'}
                  </p>
                </div>

                {/* Recording Controls */}
                <div className="flex flex-col items-center gap-4 py-4">
                  {recordings[currentPageIndex] ? (
                    <div className="flex items-center gap-4">
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => playRecording(currentPageIndex)}
                        className="w-12 h-12 rounded-full"
                      >
                        {isPlaying === currentPageIndex ? (
                          <FiPause className="w-6 h-6" />
                        ) : (
                          <FiPlay className="w-6 h-6" />
                        )}
                      </Button>
                      
                      <Button
                        variant="outline"
                        onClick={() => deleteRecording(currentPageIndex)}
                        className="gap-2"
                      >
                        <FiTrash2 className="w-4 h-4" />
                        Re-record
                      </Button>
                      
                      {!recordings[currentPageIndex].uploaded && (
                        <Button
                          onClick={() => uploadRecording(currentPageIndex)}
                          className="gap-2"
                          disabled={uploadProgress[currentPageIndex] !== undefined}
                        >
                          <FiUpload className="w-4 h-4" />
                          {uploadProgress[currentPageIndex] !== undefined
                            ? `${uploadProgress[currentPageIndex]}%`
                            : 'Upload'}
                        </Button>
                      )}
                      
                      {recordings[currentPageIndex].uploaded && (
                        <span className="text-green-500 text-sm flex items-center gap-1">
                          <FiCheck className="w-4 h-4" /> Uploaded
                        </span>
                      )}
                    </div>
                  ) : (
                    <motion.button
                      onClick={isRecording ? stopRecording : startRecording}
                      className={`w-20 h-20 rounded-full flex items-center justify-center transition-colors ${
                        isRecording
                          ? 'bg-red-500 text-white animate-pulse'
                          : 'bg-red-500/10 text-red-500 hover:bg-red-500/20'
                      }`}
                      whileTap={{ scale: 0.95 }}
                    >
                      <FiMic className="w-8 h-8" />
                    </motion.button>
                  )}
                  
                  <p className="text-sm text-muted-foreground text-center">
                    {isRecording
                      ? 'Recording... Click to stop'
                      : recordings[currentPageIndex]
                        ? 'Recording complete!'
                        : 'Click to start recording'}
                  </p>
                </div>

                {/* Upload All */}
                {hasUnuploadedRecordings && (
                  <div className="flex justify-center pt-4 border-t">
                    <Button onClick={uploadAllRecordings} className="gap-2">
                      <FiUpload className="w-4 h-4" />
                      Upload All Recordings ({Object.values(recordings).filter(r => !r.uploaded).length})
                    </Button>
                  </div>
                )}

                {/* Progress Summary */}
                <div className="text-center text-sm text-muted-foreground">
                  {Object.keys(recordings).length} of {pages.length} pages recorded
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
