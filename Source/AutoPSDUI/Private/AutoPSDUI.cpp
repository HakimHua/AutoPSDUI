// Copyright 2018-2021 - John snow wind

#include "AutoPSDUI.h"
#include "Editor.h"
#include "Subsystems/ImportSubsystem.h"
#include "EditorFramework/AssetImportData.h"

#include "AutoPSDUISetting.h"
#include "AutoPSDUILibrary.h"

#include "AssetRegistryModule.h"

#define LOCTEXT_NAMESPACE "FAutoPSDUIModule"

void FAutoPSDUIModule::StartupModule()
{
	UImportSubsystem* ImportSubsystem = GEditor->GetEditorSubsystem<UImportSubsystem>();
	ImportSubsystem->OnAssetReimport.AddRaw(this, &FAutoPSDUIModule::OnPSDImport);
}

void FAutoPSDUIModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.
}


void FAutoPSDUIModule::OnPSDImport(UObject* PSDTextureAsset)
{
	if (!UAutoPSDUISetting::Get()->bEnabled)
	{
		return;
	}

	UTexture2D* PSDTexture = Cast<UTexture2D>(PSDTextureAsset);
	if (!PSDTexture)
	{
		return;
	}
	UAssetImportData* ImportData = PSDTexture->AssetImportData;
	TArray<FString> SrcFiles;
	ImportData->ExtractFilenames(SrcFiles);
	if (SrcFiles.Num() == 0)
	{
		return;
	}

	const FString SrcFile = SrcFiles[0];

	if (!SrcFile.EndsWith(TEXT(".psd")))
	{
		return;
	}

	FString TexturePath = PSDTexture->GetPathName();
	int LastDotIndex;
	TexturePath.FindLastChar(TCHAR('.'), LastDotIndex);
	TexturePath = TexturePath.Mid(0, LastDotIndex);
	
	const FString DstFile = FPaths::Combine(
		FPaths::GetPath(TexturePath), TEXT("WBP_")
		+ FPaths::GetBaseFilename(TexturePath)
	);

	const FString PyFile = FPaths::ProjectPluginsDir() / TEXT("AutoPSDUI/Content/Python/auto_psd_ui.py");
	FString PyCmd = FString::Printf(TEXT("%s -i %s -o %s"), *PyFile, *SrcFile, *DstFile);

	UAutoPSDUILibrary::RunPyCmd(PyCmd);
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FAutoPSDUIModule, AutoPSDUI)
