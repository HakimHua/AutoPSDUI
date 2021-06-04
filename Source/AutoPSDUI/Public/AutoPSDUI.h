// Copyright 2018-2021 - John snow wind

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class FAutoPSDUIModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

protected:
	void OnPSDImport(UObject* PSDTextureAsset);
};
