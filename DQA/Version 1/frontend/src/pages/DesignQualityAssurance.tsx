import React, { useState } from 'react';
import Header from '@/components/Header';
import FileUpload from '@/components/FileUpload';
import EvaluationResults from '@/components/EvaluationResults';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

// Define interfaces based on the API response
interface ExtractedData {
  company_name: string | null;
  company_address: string | null;
  project_name: string | null;
  project_address: string | null;
  email_id: string | null;
  phone_number: string | null;
  date: string | null;
  sheet_name: string | null;
  sheet_size: string | null;
  sheet_number: string | null;
  dc_system_size: string | null;
  ac_system_size: string | null;
}

interface SystemRatingValidation {
  [key: string]: any;
}

interface AHJValidation {
  details: string;
  is_correct: "Yes" | "No" | "Uncertain";
}

interface ApiResponse {
  extracted_data: ExtractedData;
  system_rating_validation: SystemRatingValidation;
  ahj_validation: AHJValidation;
}

const DesignQualityAssurance = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationResults, setEvaluationResults] = useState<ApiResponse | null>(null);
  const { toast } = useToast();

  const handleFileSelected = (file: File) => {
    setSelectedFile(file);
    // Reset evaluation when a new file is selected
    setEvaluationResults(null);
  };

  const handleEvaluate = async () => {
    if (!selectedFile) {
      toast({
        variant: "destructive",
        title: "No file selected",
        description: "Please upload a PDF file to evaluate."
      });
      return;
    }

    setIsEvaluating(true);
    
    try {
      // Create FormData to send the file
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      // Make API call to your Flask backend
      const response = await fetch('http://localhost:5000/validate-pdf', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('API response was not ok');
      }
      
      const data = await response.json();
      setEvaluationResults(data);
      
      toast({
        title: "Evaluation complete",
        description: "Your design has been evaluated successfully."
      });
    } catch (error) {
      console.error('Error during evaluation:', error);
      toast({
        variant: "destructive",
        title: "Evaluation failed",
        description: "An error occurred during the evaluation process."
      });
    } finally {
      setIsEvaluating(false);
    }
  };

  const resetEvaluation = () => {
    setSelectedFile(null);
    setEvaluationResults(null);
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      
      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {!evaluationResults ? (
            <>
              <div className="text-center mb-8">
                <h1 className="text-3xl font-bold mb-2">Solar Plan Validation</h1>
                <p className="text-gray-600">
                  Upload your Plan Set to validate system specs and code compliance
                </p>
              </div>
              
              <Card>
                <CardContent className="pt-6">
                  <FileUpload onFileSelected={handleFileSelected} />
                  
                  <div className="mt-6 flex justify-center">
                    <Button 
                      onClick={handleEvaluate} 
                      disabled={!selectedFile || isEvaluating} 
                      className="bg-gold-500 hover:bg-gold-600 text-white"
                    >
                      {isEvaluating ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Validating...
                        </>
                      ) : (
                        'Validate Plan Set'
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
              
              {isEvaluating && (
                <div className="mt-8 text-center">
                  <div className="inline-block rounded-lg bg-white p-6 shadow-md">
                    <Loader2 className="h-10 w-10 animate-spin mx-auto mb-4 text-gold-500" />
                    <h3 className="text-lg font-medium">Analyzing your plan set...</h3>
                    <p className="text-sm text-gray-500 mt-2">
                      This may take up to a minute as we validate system specs and code compliance
                    </p>
                  </div>
                </div>
              )}
            </>
          ) : (
            <>
              <div className="mb-6 flex justify-between items-center">
                <h1 className="text-2xl font-bold">Validation Results</h1>
                <Button 
                  variant="outline" 
                  onClick={resetEvaluation}
                >
                  Validate Another Plan Set
                </Button>
              </div>
              
              <EvaluationResults 
                evaluation={evaluationResults} 
                fileName={selectedFile?.name} 
              />
            </>
          )}
        </div>
      </main>
      
      <footer className="bg-white border-t border-gray-200 py-4">
        <div className="container mx-auto px-4 text-center text-sm text-gray-500">
          © {new Date().getFullYear()} Solar Plan Validator. All rights reserved.
        </div>
      </footer>
    </div>
  );
};

export default DesignQualityAssurance;