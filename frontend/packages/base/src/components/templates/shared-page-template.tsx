import React from 'react';
import { Separator } from '../ui/separator';

export interface PageTemplateConfig {
  title: string;
  fetchData: (projectId?: string) => Promise<any>;
  TableComponent: React.ComponentType<any>;
  NoProjectComponent?: React.ComponentType<{ title: string }>;
  requiresProject?: boolean;
  useSeparator?: boolean;
  errorFallback?: any;
  tableProps?: Record<string, any>;
}

export interface SharedPageTemplateProps {
  config: PageTemplateConfig;
  searchParams?: { project?: string };
  projectId?: string;
}

export async function SharedPageTemplate({ 
  config, 
  searchParams, 
  projectId: directProjectId 
}: SharedPageTemplateProps) {
  const {
    title,
    fetchData,
    TableComponent,
    NoProjectComponent,
    requiresProject = false,
    useSeparator = true,
    errorFallback = [],
    tableProps = {}
  } = config;

  // Handle project validation for SaaS
  const projectId = directProjectId || searchParams?.project;
  
  if (requiresProject && !projectId) {
    if (NoProjectComponent) {
      return <NoProjectComponent title={title} />;
    }
    return null;
  }

  // Fetch data with error handling
  let data;
  try {
    data = await fetchData(projectId);
  } catch (error) {
    console.error(error);
    data = errorFallback;
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-4 lg:gap-6 lg:p-6">
      <div className="flex flex-col gap-4">
        <h1 className="text-lg font-semibold md:text-2xl">{title}</h1>
        {useSeparator && <Separator />}
      </div>
      <TableComponent 
        {...(title.toLowerCase().includes('policies') ? { policies: data } : { dataSources: data })}
        {...(projectId && { projectId })}
        {...tableProps}
      />
    </div>
  );
}