import React from 'react';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Clock, CheckCircle, AlertCircle, FileText, Calendar, AlertTriangle, Map, MapPin, Compass } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Image from 'next/image';

// Define interfaces based on the app.py API response
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
  [key: string]: any; // This will capture the rating validation response
}

interface AHJValidation {
  details: string;
  is_correct: "Yes" | "No" | "Uncertain";
}

interface ValidationResult {
  pdf_image: string;
  google_image: string;
  results: {
    "Map Match (%)": string;
    "Satellite Match (%)": string;
    "Key Differences": string;
    "Key Similarities": string;
    "Confidence": string;
    "Conclusion": string;
  };
}

interface LocationValidation {
  success: boolean;
  error?: string;
  address?: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  reference_maps?: {
    map: string;
    satellite: string;
  };
  extracted_images?: {
    map_views: string[];
    satellite_views: string[];
    other: string[];
  };
  validation_results?: {
    map_validations: ValidationResult[];
    satellite_validations: ValidationResult[];
  };
}

interface ComparisonResult {
  Specification: string;
  "Extracted Data Value": string;
  "Validated Data from Search": string;
  Status: string;
}

interface ComparisonResults {
  [category: string]: ComparisonResult[];
}

interface StructuredData {
  [category: string]: {
    [spec: string]: string;
  };
}

interface WebData {
  summary: string;
  top_links: string[];
}

// Update ApiResponse to include new fields
interface ApiResponse {
  extracted_data: ExtractedData;
  system_rating_validation: SystemRatingValidation;
  ahj_validation: AHJValidation;
  location_validation: LocationValidation;
  fileName?: string;
  uploadDate?: Date;
  comparison_results?: ComparisonResults;
  structured_data?: StructuredData;
  web_data?: WebData;
}

interface EvaluationResultsProps {
  evaluation: ApiResponse | null;
  fileName?: string;
  baseUrl?: string; // For handling server base URL
}

const EvaluationResults: React.FC<EvaluationResultsProps> = ({ 
  evaluation, 
  fileName,
  baseUrl = '' // Default to empty string for relative paths
}) => {
  if (!evaluation) return null;
  
  const { 
    comparison_results, 
    structured_data, 
    web_data, 
    extracted_data, 
    system_rating_validation, 
    ahj_validation, 
    location_validation 
  } = evaluation;
  
  // Extract system rating validation text
  let systemRatingText = "";
  if (typeof system_rating_validation === 'string') {
    systemRatingText = system_rating_validation;
  } else if (system_rating_validation && typeof system_rating_validation === 'object') {
    // Try to extract meaningful text from the object
    if ('error' in system_rating_validation) {
      systemRatingText = system_rating_validation.error as string;
    } else {
      // Try to get any string property from the object
      const firstStringProp = Object.values(system_rating_validation).find(val => typeof val === 'string');
      systemRatingText = firstStringProp || JSON.stringify(system_rating_validation);
    }
  }
  
  // Check if system rating contains a discrepancy
  // const hasRatingDiscrepancy = systemRatingText.includes("Discrepancy");
  const hasRatingDiscrepancy = system_rating_validation["System Rating Check"]?.toLowerCase().includes("discrepancy");

  const isAHJValid = ahj_validation?.is_correct === "Yes";
  
  // Determine if location validation is successful
  const isLocationValid = location_validation?.success && 
    location_validation?.validation_results && 
    ((location_validation.validation_results.map_validations?.length > 0) || 
     (location_validation.validation_results.satellite_validations?.length > 0));
  
  // Get location match percentages
  const getLocationMatchScore = () => {
    if (!isLocationValid || !location_validation.validation_results) return 0;
    
    let totalScore = 0;
    let count = 0;
    
    // Process map validations if they exist
    if (location_validation.validation_results.map_validations) {
      location_validation.validation_results.map_validations.forEach(validation => {
        const matchPercent = parseFloat(validation.results["Map Match (%)"].replace('%', ''));
        if (!isNaN(matchPercent)) {
          totalScore += matchPercent;
          count++;
        }
      });
    }
    
    // Process satellite validations if they exist
    if (location_validation.validation_results.satellite_validations) {
      location_validation.validation_results.satellite_validations.forEach(validation => {
        const matchPercent = parseFloat(validation.results["Satellite Match (%)"].replace('%', ''));
        if (!isNaN(matchPercent)) {
          totalScore += matchPercent;
          count++;
        }
      });
    }
    
    return count > 0 ? totalScore / count : 0;
  };
  
  const locationMatchScore = getLocationMatchScore();
  const locationStatus = locationMatchScore >= 80 ? "Passed" : locationMatchScore >= 50 ? "Warning" : "Failed";
  
  // Calculate overall validation score
  let validationScore = 0;
  let maxScore = 3; // Total number of validations (including location)
  
  if (!hasRatingDiscrepancy) validationScore++;
  if (isAHJValid) validationScore++;
  if (locationMatchScore >= 70) validationScore++;
  
  const scorePct = (validationScore / maxScore) * 100;
  
  let statusBadge;
  if (scorePct === 100) {
    statusBadge = <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" /> Passed</Badge>;
  } else if (scorePct >= 66) {
    statusBadge = <Badge className="bg-amber-100 text-amber-800"><AlertTriangle className="h-3 w-3 mr-1" /> Warnings</Badge>;
  } else {
    statusBadge = <Badge className="bg-red-100 text-red-800"><AlertCircle className="h-3 w-3 mr-1" /> Failed</Badge>;
  }

  // Helper function to get image URL
  const getImageUrl = (path: string) => {
    // Remove "uploads/" from the beginning if present
    const relativePath = path.replace(/^uploads\//, '');
    // Construct the full URL
    return `${baseUrl}/uploads/${relativePath}`;
  };
  
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">Plan Set Validation Results</h2>
          {/* Only render structured data if it exists */}
          {structured_data && (
            <div className="mb-8">
              <h3 className="text-xl font-semibold mb-2">Structured Data</h3>
              {Object.entries(structured_data).map(([category, specs]) => (
                <div key={category} className="mb-4">
                  <h4 className="text-lg font-semibold mb-2">{category}</h4>
                  <table className="w-full bg-white shadow-md rounded-lg">
                    <thead className="bg-gray-300">
                      <tr>
                        <th className="p-2 text-left">Specification</th>
                        <th className="p-2 text-left">Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(specs).map(([spec, value]) => (
                        <tr key={spec} className="border-b">
                          <td className="p-2">{spec}</td>
                          <td className="p-2">{value}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </div>
          )}
          
          {/* Only render web data if it exists */}
          {web_data && (
            <div>
              <h3 className="text-xl font-semibold mb-2">Web Data</h3>
              {web_data.summary.split("\n\n").map((section, sectionIndex) => {
                const lines = section.split("\n");
                return (
                  <div key={sectionIndex} className="mb-4">
                    <h4 className="text-lg font-semibold">{lines[0]}</h4>
                    <ul className="list-disc pl-5">
                      {lines.slice(1).map((line, index) =>
                        line.trim() ? (
                          <li key={index} className="mb-1">
                            {line}
                          </li>
                        ) : null
                      )}
                    </ul>
                  </div>
                );
              })}

              <h4 className="text-lg font-semibold mt-3">Reference Links</h4>
              <ul className="list-disc pl-5">
                {web_data.top_links.map((link, index) => (
                  <li key={index} className="text-blue-500 underline">
                    <a href={link} target="_blank" rel="noopener noreferrer">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Only render comparison results if they exist */}
          {comparison_results && (
            <div className="mb-8">
              <h3 className="text-xl font-semibold mb-2">Comparison Results</h3>
              {Object.entries(comparison_results).map(([category, results]) => (
                <div key={category} className="mb-4">
                  <h4 className="text-lg font-semibold mb-2">{category}</h4>
                  <table className="w-full bg-white shadow-md rounded-lg">
                    <thead className="bg-gray-300">
                      <tr>
                        <th className="p-2 text-left">Specification</th>
                        <th className="p-2 text-left">Extracted Data Value</th>
                        <th className="p-2 text-left">Validated Data from Search</th>
                        <th className="p-2 text-left">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.map(
                        ({
                          Specification,
                          "Extracted Data Value": extracted,
                          "Validated Data from Search": validated,
                          Status,
                        }) => (
                          <tr key={Specification} className="border-b">
                            <td className="p-2">{Specification}</td>
                            <td className="p-2">{extracted}</td>
                            <td className="p-2">{validated}</td>
                            <td className="p-2">{Status}</td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>
              ))}
            </div>
          )}
          <div className="flex items-center gap-2 mt-1">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{fileName || 'Unnamed File'}</span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              {new Date().toLocaleDateString()} at {new Date().toLocaleTimeString()}
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end">
          {statusBadge}
          <div className="mt-2 flex items-center gap-2">
            <div className="text-3xl font-bold">
              {validationScore}/{maxScore}
            </div>
            <div className="text-sm">
              ({scorePct.toFixed(0)}%)
            </div>
          </div>
        </div>
      </div>
      
      {/* Project Information Card */}
      {extracted_data && (
        <Card>
          <CardHeader>
            <CardTitle>Project Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="font-semibold">Company</h3>
                <p>{extracted_data.company_name || 'Not found'}</p>
                <p className="text-sm text-muted-foreground">{extracted_data.company_address || 'Address not found'}</p>
              </div>
              <div>
                <h3 className="font-semibold">Project</h3>
                <p>{extracted_data.project_name || 'Not found'}</p>
                <p className="text-sm text-muted-foreground">{extracted_data.project_address || 'Address not found'}</p>
              </div>
              <div>
                <h3 className="font-semibold">Contact</h3>
                <p>{extracted_data.email_id || 'No email found'}</p>
                <p>{extracted_data.phone_number || 'No phone found'}</p>
              </div>
              <div>
                <h3 className="font-semibold">System Size</h3>
                <p>DC: {extracted_data.dc_system_size || 'Not specified'}</p>
                <p>AC: {extracted_data.ac_system_size || 'Not specified'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* System Rating Validation Card */}
{/* System Rating Validation Card */}
{system_rating_validation && (
  <Card className="mb-4">
    <CardHeader className="pb-2">
      <div className="flex items-start justify-between">
        <div>
          <CardTitle className="text-base">System Rating Validation</CardTitle>
          <CardDescription className="text-xs">
            Verifying if the stated DC system rating matches the calculated value
          </CardDescription>
        </div>
        <Badge className={
          hasRatingDiscrepancy 
            ? 'bg-red-100 text-red-800'   // Failed (Discrepancy Found)
            : 'bg-green-100 text-green-800' // Passed (No Discrepancy)
        }>
          {hasRatingDiscrepancy ? 'Failed' : 'Passed'}
        </Badge>
      </div>
    </CardHeader>
    <CardContent>
      <div className="space-y-2">
        <Progress
          value={hasRatingDiscrepancy ? 0 : 100}
          className={`h-2 ${hasRatingDiscrepancy ? 'bg-red-500' : 'bg-green-500'}`}
        />

        {/* Properly ordered validation details */}
        {[
          { key: "System Rating Check", label: "System Rating Check" },
          { key: "Newly Installed Modules", label: "Newly Installed Modules" },
          { key: "Stated DC System Rating (kWDC)", label: "Stated DC System Rating" },
          { key: "Expected kWDC Calculation", label: "Calculated kWDC" }, // Renamed
          { key: "Stated AC System Rating (kWAC)", label: "Stated AC System Rating" },
          // { key: "Efficiency Calculation", label: "Efficiency Calculation" },
          { key: "Efficiency", label: "Efficiency (%)" },
        ].map(({ key, label }) =>
          system_rating_validation[key] ? (
            <div key={key} className="flex justify-between text-sm border-b py-1">
              <span className="font-medium">{label}:</span>
              <span className="text-right">{String(system_rating_validation[key])}</span>
            </div>
          ) : null
        )}
      </div>
    </CardContent>
  </Card>
)}


      
      {/* AHJ Code Validation Card */}
{ahj_validation && (
  <Card className="mb-4">
    <CardHeader className="pb-2">
      <div className="flex items-start justify-between">
        <div>
          <CardTitle className="text-base">AHJ Code Validation</CardTitle>
          <CardDescription className="text-xs">
            Verifying if the governing codes are correct for the Authority Having Jurisdiction
          </CardDescription>
        </div>
        <Badge className={
          ahj_validation.is_correct === "Yes" ? 'bg-green-100 text-green-800' : 
          ahj_validation.is_correct === "No" ? 'bg-red-100 text-red-800' : 
          'bg-amber-100 text-amber-800'
        }>
          {ahj_validation.is_correct}
        </Badge>
      </div>
    </CardHeader>
    <CardContent>
      <div className="space-y-2">
        <Progress 
          value={
            ahj_validation.is_correct === "Yes" ? 100 : 
            ahj_validation.is_correct === "No" ? 0 : 
            50
          } 
          className={`h-2 ${
            ahj_validation.is_correct === "Yes" ? 'bg-green-500' : 
            ahj_validation.is_correct === "No" ? 'bg-red-500' : 
            'bg-amber-500'
          }`}
        />

        {/* Display structured validation details */}
        <div className="space-y-2 text-sm">
          <h3 className="font-semibold">Mentioned Governing Codes:</h3>
          <ul className="list-disc pl-5">
            {ahj_validation.details.match(/\*\*(.*?)\*\*/g)?.map((code, index) => (
              <li key={index}>{code.replace(/\*\*/g, '')}</li>
            ))}
          </ul>
        </div>

        <div className="space-y-2 text-sm">
          <h3 className="font-semibold">Validation Summary:</h3>
          <p>
            {ahj_validation.details.split("Trusted sources for validation include:")[0]
              .replace(/\*\*(.*?)\*\*/g, (_, code) => `<strong>${code}</strong>`)
              .replace(/\[([0-9])\]/g, '')}
          </p>
        </div>

        {/* Display trusted sources separately */}
        <div className="space-y-2 text-sm">
          <h3 className="font-semibold">Trusted Sources:</h3>
          <ul className="list-disc pl-5">
            {ahj_validation.details.match(/\[(https:\/\/.*?)\]/g)?.map((source, index) => (
              <li key={index}>
                <a 
                  href={source.replace(/[\[\]]/g, '')} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="text-blue-500 underline"
                >
                  {source.replace(/[\[\]]/g, '')}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </CardContent>
  </Card>
)}

      
      {/* Location Validation Card */}
      {location_validation && (
        <Card className="mb-4">
          <CardHeader className="pb-2">
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-base">Location Validation</CardTitle>
                <CardDescription className="text-xs">
                  Verifying if the project location in the plans matches the actual address
                </CardDescription>
              </div>
              <Badge className={
                !location_validation.success ? 'bg-red-100 text-red-800' :
                locationStatus === "Passed" ? 'bg-green-100 text-green-800' :
                locationStatus === "Warning" ? 'bg-amber-100 text-amber-800' :
                'bg-red-100 text-red-800'
              }>
                {!location_validation.success ? 'Error' : locationStatus}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            {!location_validation.success ? (
              <div className="space-y-2">
                <Progress value={0} className="h-2 bg-red-500" />
                <p className="text-sm text-red-600">
                  {location_validation.error || "Failed to validate location"}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Progress 
                    value={locationMatchScore} 
                    className={`h-2 ${
                      locationStatus === "Passed" ? 'bg-green-500' :
                      locationStatus === "Warning" ? 'bg-amber-500' :
                      'bg-red-500'
                    }`}
                  />
                  
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">
                      <strong>Extracted Address:</strong> {location_validation.address || "Not found"}
                    </span>
                  </div>
                  
                  {location_validation.coordinates && (
                    <div className="flex items-center gap-2">
                      <Compass className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">
                        <strong>Coordinates:</strong> {location_validation.coordinates.latitude.toFixed(6)}, {location_validation.coordinates.longitude.toFixed(6)}
                      </span>
                    </div>
                  )}
                </div>
                
                {/* Image Comparison Tabs */}
                {location_validation.validation_results && 
                  (location_validation.validation_results.map_validations?.length > 0 || 
                   location_validation.validation_results.satellite_validations?.length > 0) && (
                  <Tabs defaultValue="maps" className="w-full">
                    <TabsList>
                      <TabsTrigger 
                        value="maps" 
                        disabled={!location_validation.validation_results.map_validations?.length}
                      >
                        Map Views ({location_validation.validation_results.map_validations?.length || 0})
                      </TabsTrigger>
                      <TabsTrigger 
                        value="satellite" 
                        disabled={!location_validation.validation_results.satellite_validations?.length}
                      >
                        Satellite Views ({location_validation.validation_results.satellite_validations?.length || 0})
                      </TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="maps" className="space-y-4 mt-4">
                      {location_validation.validation_results.map_validations?.map((validation, index) => (
                        <div key={`map-${index}`} className="border rounded-lg p-3">
                          <div className="text-sm font-medium mb-2">Map Comparison #{index + 1}</div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <div className="text-xs text-muted-foreground">PDF Map</div>
                              <div className="border rounded overflow-hidden h-48 relative">
                                <img
                                  src={getImageUrl(validation.pdf_image)}
                                  alt="PDF Map"
                                  className="object-contain w-full h-full"
                                />
                              </div>
                            </div>
                            <div className="space-y-2">
                              <div className="text-xs text-muted-foreground">Google Map</div>
                              <div className="border rounded overflow-hidden h-48 relative">
                                <img
                                  src={getImageUrl(validation.google_image)}
                                  alt="Google Map"
                                  className="object-contain w-full h-full"
                                />
                              </div>
                            </div>
                          </div>
                          <div className="mt-3 space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Match Score:</span>
                              <span className="text-sm font-bold">{validation.results["Map Match (%)"]}</span>
                            </div>
                            <div className="text-xs">
                              <strong>Confidence:</strong> {validation.results["Confidence"]}
                            </div>
                            <div className="text-xs">
                              <strong>Conclusion:</strong> {validation.results["Conclusion"]}
                            </div>
                          </div>
                        </div>
                      ))}
                    </TabsContent>
                    
                    <TabsContent value="satellite" className="space-y-4 mt-4">
                      {location_validation.validation_results.satellite_validations?.map((validation, index) => (
                        <div key={`satellite-${index}`} className="border rounded-lg p-3">
                          <div className="text-sm font-medium mb-2">Satellite Comparison #{index + 1}</div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <div className="text-xs text-muted-foreground">PDF Satellite</div>
                              <div className="border rounded overflow-hidden h-48 relative">
                                <img
                                  src={getImageUrl(validation.pdf_image)}
                                  alt="PDF Satellite"
                                  className="object-contain w-full h-full"
                                />
                              </div>
                            </div>
                            <div className="space-y-2">
                              <div className="text-xs text-muted-foreground">Google Satellite</div>
                              <div className="border rounded overflow-hidden h-48 relative">
                                <img
                                  src={getImageUrl(validation.google_image)}
                                  alt="Google Satellite"
                                  className="object-contain w-full h-full"
                                />
                              </div>
                            </div>
                          </div>
                          <div className="mt-3 space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Match Score:</span>
                              <span className="text-sm font-bold">{validation.results["Satellite Match (%)"]}</span>
                            </div>
                            <div className="text-xs">
                              <strong>Confidence:</strong> {validation.results["Confidence"]}
                            </div>
                            <div className="text-xs">
                              <strong>Conclusion:</strong> {validation.results["Conclusion"]}
                            </div>
                          </div>
                        </div>
                      ))}
                    </TabsContent>
                  </Tabs>
                )}
              </div>
            )}
            
          </CardContent>
        </Card>
        
      )}
    </div>
  );
};

export default EvaluationResults;