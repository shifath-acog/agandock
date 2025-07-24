'use client';

import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Upload, FileText, CheckCircle, Play, X, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Custom validator for File type to avoid SSR issues
const isFile = (value: any): value is File => {
  if (typeof window === 'undefined') return true; // Skip on server
  return value instanceof File;
};

// Zod schema for form validation
const dockingFormSchema = z
  .object({
    folderName: z.string().min(1, 'Output folder is required').regex(/^[a-zA-Z0-9_-]+$/, 'Folder name must contain only letters, numbers, underscores, or hyphens'),
    pdbFile: z.any().refine(isFile, { message: 'PDB file is required' }),
    pdbqtFile: z.any().refine(isFile, { message: 'PDBQT file is required' }),
    configFile: z.any().refine(isFile, { message: 'Configuration file is required' }),
    inputType: z.enum(['csv', 'smiles']),
    inputCsv: z.any().optional(),
    inputSmiles: z.string().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.inputType === 'csv' && !isFile(data.inputCsv)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'A CSV file is required for this input type.',
        path: ['inputCsv'],
      });
    }
    if (data.inputType === 'smiles') {
      if (!data.inputSmiles || data.inputSmiles.trim() === '') {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'A SMILES string is required for this input type.',
          path: ['inputSmiles'],
        });
      } else if (data.inputSmiles.includes('\n')) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Only a single SMILES string is allowed (no newlines).',
          path: ['inputSmiles'],
        });
      }
    }
  });

type DockingFormValues = z.infer<typeof dockingFormSchema>;

interface MolecularDockingFormProps {
  onSubmit: (data: DockingFormValues) => Promise<void>;
}

export function MolecularDockingForm({ onSubmit }: MolecularDockingFormProps) {
  const [inputType, setInputType] = useState<'csv' | 'smiles'>('csv');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [draggedOver, setDraggedOver] = useState<string | null>(null);

  const form = useForm<DockingFormValues>({
    resolver: zodResolver(dockingFormSchema),
    defaultValues: {
      folderName: 'agandock_test_api',
      inputType: 'csv',
      inputSmiles: '', // Initialize as empty string to prevent uncontrolled input
      inputCsv: undefined,
    },
  });

  const handleTabChange = (value: 'csv' | 'smiles') => {
    setInputType(value);
    form.setValue('inputType', value);
    // Explicitly set fields to prevent uncontrolled/controlled transition
    form.setValue('inputSmiles', value === 'smiles' ? '' : undefined);
    form.setValue('inputCsv', value === 'csv' ? undefined : undefined);
    form.trigger(); // Re-validate the form
  };

  const handleSubmit = async (data: DockingFormValues) => {
    setIsSubmitting(true);
    try {
      await onSubmit(data);
    } finally {
      setIsSubmitting(false);
    }
  };

  const removeFile = (fieldName: keyof DockingFormValues) => {
    form.setValue(fieldName, undefined, { shouldValidate: true });
  };

  const FileUploadField = ({
    name,
    label,
    description,
    accept,
  }: {
    name: keyof DockingFormValues;
    label: string;
    description: string;
    accept: string;
  }) => {
    const isDragged = draggedOver === name;

    return (
      <FormField
        control={form.control}
        name={name}
        render={({ field }) => {
          const uploadedFile = field.value as File | undefined;

          return (
            <FormItem className="group">
              <FormLabel className="text-sm font-semibold text-gray-700 group-hover:text-blue-600 transition-colors duration-200">
                {label}
              </FormLabel>
              <FormControl>
                <div className="relative">
                  <div className="flex items-center justify-center w-full">
                    <label
                      className={`
                        relative flex flex-col items-center justify-center w-full h-24 border-2 border-dashed rounded-xl cursor-pointer
                        transition-all duration-300 ease-in-out bg-white shadow-sm hover:shadow-md
                        ${
                          isDragged
                            ? 'border-blue-500 bg-blue-50/50 scale-[1.02]'
                            : uploadedFile
                              ? 'border-green-400 bg-green-50/30 hover:bg-green-50'
                              : 'border-gray-300 hover:bg-gray-50 hover:border-gray-400'
                        }
                      `}
                      onDragOver={(e) => {
                        e.preventDefault();
                        setDraggedOver(name);
                      }}
                      onDragLeave={() => setDraggedOver(null)}
                      onDrop={(e) => {
                        e.preventDefault();
                        setDraggedOver(null);
                        const files = e.dataTransfer.files;
                        if (files.length > 0) {
                          field.onChange(files[0]);
                        }
                      }}
                    >
                      <div className="flex flex-col items-center justify-center py-3">
                        <Upload
                          className={`w-6 h-6 mb-2 transition-all duration-300 ${
                            isDragged ? 'text-blue-500 scale-110' : 'text-gray-500'
                          }`}
                        />
                        <p className="text-sm text-gray-600 font-medium">
                          <span className="font-semibold">Click to upload</span> or drag and drop
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {accept.replace(/\./g, '').toUpperCase()} files
                        </p>
                      </div>
                      <Input
                        type="file"
                        accept={accept}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                            field.onChange(file);
                          }
                        }}
                      />
                    </label>
                  </div>

                  {/* {uploadedFile && (
                    <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-xl shadow-sm animate-in slide-in-from-top-2 duration-300">
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 flex-1">
                          <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 animate-in zoom-in duration-300" />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-green-800">Upload successful!</p>
                            <p className="text-xs text-green-700 flex items-center gap-1 mt-1 truncate">
                              <FileText className="h-4 w-4 flex-shrink-0" />
                              {uploadedFile.name}
                            </p>
                          </div>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0 hover:bg-red-100 hover:text-red-600 transition-colors duration-200"
                          onClick={(e) => {
                            e.stopPropagation();
                            removeFile(name);
                          }}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )} */}
                </div>
              </FormControl>
              {description && (
                <FormDescription className="text-xs text-gray-500 mt-2 transition-colors group-hover:text-gray-600">
                  {description}
                </FormDescription>
              )}
              <FormMessage className="text-xs text-red-500 mt-2" />
            </FormItem>
          );
        }}
      />
    );
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl mt-2">
<Card className="border-0 shadow-xl shadow-[0_-4px_16px_-4px_rgba(0,0,0,0.10)] hover:shadow-2xl hover:shadow-[0_-8px_24px_-6px_rgba(0,0,0,0.13)] transition-shadow duration-300 bg-white rounded-2xl overflow-hidden">
        <CardContent className="px-8 py-10">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-10">
              {/* Output Folder Section */}
              <div className="space-y-6 animate-in fade-in slide-in-from-left-4 duration-500 delay-100 border border-gray-200 shadow-md hover:shadow-lg transition-shadow duration-200 bg-white rounded-xl px-6 py-4">
                <div className="border-b border-gray-200 pb-4">
                  <h3 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
                    <FileText className="h-5 w-5 text-blue-600" />
                    Output Directory
                  </h3>
                  <p className="text-sm text-gray-600 mt-2">Specify the directory where docking results will be saved</p>
                </div>
                <FormField
                  control={form.control}
                  name="folderName"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-sm font-semibold text-gray-700">Output Folder Name</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="agandock_test_api"
                          className="w-full h-12 border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-500 transition-all duration-200"
                          {...field}
                        />
                      </FormControl>
                      <FormDescription className="text-xs text-gray-500 mt-2">
                        Enter a folder name for results (e.g., docking_test_1). It will be created under /app/.
                      </FormDescription>
                      <FormMessage className="text-xs text-red-500 mt-2" />
                    </FormItem>
                  )}
                />
              </div>

              {/* File Upload Section */}
              <div className="space-y-6 animate-in fade-in slide-in-from-left-4 duration-500 delay-200 border border-gray-200 shadow-md hover:shadow-lg transition-shadow duration-200 bg-white rounded-xl px-6 py-4">
                <div className="border-b border-gray-200 pb-4">
                  <h3 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
                    <FileText className="h-5 w-5 text-blue-600" />
                    Molecular Files
                  </h3>
                  <p className="text-sm text-gray-600 mt-2">Upload the required molecular structure files</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <FileUploadField
                    name="pdbFile"
                    label="PDB File"
                    description=""
                    accept=".pdb"
                  />
                  <FileUploadField
                    name="pdbqtFile"
                    label="PDBQT File"
                    description=""
                    accept=".pdbqt"
                  />
                </div>
                <FileUploadField
                  name="configFile"
                  label="Configuration File"
                  description="Upload docking configuration file (.txt, .conf)"
                  accept=".txt,.conf"
                />
              </div>

              {/* Input Type Section */}
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500 delay-400 border border-gray-200 shadow-md hover:shadow-lg transition-shadow duration-200 bg-white rounded-xl px-6 py-4">
                <div className="border-b border-gray-200 pb-4">
                  <h3 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
                    <Upload className="h-5 w-5 text-green-600" />
                    Ligand Input
                  </h3>
                  <p className="text-sm text-gray-600 mt-2">Choose how to provide ligand information</p>
                </div>
                <Tabs
                  value={inputType}
                  onValueChange={(value) => handleTabChange(value as 'csv' | 'smiles')}
                  className="w-full"
                >
                  <TabsList className="grid w-full grid-cols-2 h-14 p-1 bg-gray-100 rounded-xl shadow-sm">
                    <TabsTrigger
                      value="csv"
                      className="h-12 text-sm font-semibold data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-blue-600 transition-all duration-200 hover:bg-gray-200 rounded-lg"
                    >
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        CSV File
                      </div>
                    </TabsTrigger>
                    <TabsTrigger
                      value="smiles"
                      className="h-12 text-sm font-semibold data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-blue-600 transition-all duration-200 hover:bg-gray-200 rounded-lg"
                    >
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        SMILES String
                      </div>
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="csv" className="mt-8 animate-in fade-in slide-in-from-left-2 duration-300">
                    <Card className="border border-gray-200 shadow-md hover:shadow-lg transition-shadow duration-200 bg-white rounded-xl">
                      <CardHeader className="pb-4">
                        <CardTitle className="text-lg font-semibold text-gray-800">Upload CSV File</CardTitle>
                        <CardDescription className="text-sm text-gray-600">
                          Upload a CSV file containing ligand data for batch processing
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="pt-2">
                        <FileUploadField
                          name="inputCsv"
                          label="Ligand CSV File"
                          description="Upload CSV file with ligand information (.csv)"
                          accept=".csv"
                        />
                      </CardContent>
                    </Card>
                  </TabsContent>

                  <TabsContent value="smiles" className="mt-8 animate-in fade-in slide-in-from-right-2 duration-300">
                    <Card className="border border-gray-200 shadow-md hover:shadow-lg transition-shadow duration-200 bg-white rounded-xl">
                      <CardHeader className="pb-4">
                        <CardTitle className="text-lg font-semibold text-gray-800">Enter SMILES String</CardTitle>
                        <CardDescription className="text-sm text-gray-600">
                          Enter a single SMILES string for the ligand
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="pt-2">
                        <FormField
                          control={form.control}
                          name="inputSmiles"
                          render={({ field }) => (
                            <FormItem className="group">
                              <FormLabel className="text-sm font-semibold text-gray-700 group-hover:text-blue-600 transition-colors duration-200">
                                SMILES Notation
                              </FormLabel>
                              <FormControl>
                                <Input
                                  placeholder="e.g., CCO (ethanol)"
                                  className="w-full h-12 border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-500 transition-all duration-200 hover:border-gray-400 font-mono text-sm"
                                  {...field}
                                />
                              </FormControl>
                              <FormDescription className="text-xs text-gray-500 mt-2 group-hover:text-gray-600">
                                Enter a single SMILES string (e.g., CCO). Multiple SMILES are not supported.
                              </FormDescription>
                              <FormMessage className="text-xs text-red-500 mt-2" />
                            </FormItem>
                          )}
                        />
                      </CardContent>
                    </Card>
                  </TabsContent>
                </Tabs>
              </div>

              {/* Submit Button */}
              <div className="pt-8 border-t border-gray-200 animate-in fade-in slide-in-from-bottom-2 duration-500 delay-600">
                <Button
                  type="submit"
                  size="lg"
                  className="w-full h-14 text-lg font-semibold hover:to-purple-700 text-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] disabled:scale-100 disabled:opacity-50"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-6 w-6 mr-2 animate-spin" />
                      Running Docking...
                    </>
                  ) : (
                    <>
                      <Play className="h-6 w-6 mr-2" />
                      Run Docking Pipeline
                    </>
                  )}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}