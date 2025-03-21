
import React, { useState, useRef, DragEvent } from 'react';
import { UploadCloud, File, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

interface FileUploadProps {
  onFileSelected: (file: File) => void;
  accept?: string;
  maxSize?: number; // in MB
}

const FileUpload: React.FC<FileUploadProps> = ({ 
  onFileSelected, 
  accept = '.pdf', 
  maxSize = 50 // 5MB default
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const validateFile = (file: File): boolean => {
    // Reset previous errors
    setError(null);
    
    // Check file type
    if (accept && !file.name.endsWith('.pdf')) {
      setError(`Please upload a PDF file.`);
      toast({
        variant: "destructive",
        title: "Invalid file type",
        description: "Please upload a PDF file."
      });
      return false;
    }
    
    // Check file size
    if (maxSize && file.size > maxSize * 1024 * 1024) {
      setError(`File size exceeds ${maxSize}MB limit.`);
      toast({
        variant: "destructive",
        title: "File too large",
        description: `File size exceeds ${maxSize}MB limit.`
      });
      return false;
    }
    
    return true;
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
        onFileSelected(file);
        toast({
          title: "File uploaded",
          description: `${file.name} has been uploaded successfully.`
        });
      }
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
        onFileSelected(file);
        toast({
          title: "File uploaded",
          description: `${file.name} has been uploaded successfully.`
        });
      }
    }
  };

  const handleButtonClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className="w-full">
      <div
        className={`file-drop-area ${isDragging ? 'drag-active' : 'border-gray-300 hover:border-gold-400'}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleButtonClick}
      >
        <input
          type="file"
          className="hidden"
          ref={fileInputRef}
          accept={accept}
          onChange={handleFileInputChange}
        />
        
        <div className="flex flex-col items-center justify-center gap-3">
          {selectedFile ? (
            <>
              <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
                <File className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm font-medium">{selectedFile.name}</p>
                <p className="text-xs text-gray-500">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedFile(null);
                }}
              >
                Choose another file
              </Button>
            </>
          ) : (
            <>
              <div className="h-12 w-12 rounded-full bg-gold-100 flex items-center justify-center">
                <UploadCloud className="h-6 w-6 text-gold-600" />
              </div>
              <div className="space-y-1 text-center">
                <p className="text-sm font-medium">Drag & drop your PDF file here</p>
                <p className="text-xs text-gray-500">
                  or click to browse (max {maxSize}MB)
                </p>
              </div>
            </>
          )}
        </div>
      </div>
      
      {error && (
        <div className="mt-2 flex items-center gap-2 text-destructive text-sm">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};

export default FileUpload;